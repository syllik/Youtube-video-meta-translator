"""Process-local, cancellable Codex generation jobs for the Streamlit UI."""

import copy
import threading
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Deque, Mapping, Optional, Sequence, Tuple

from codex_localization_generator import (
    CodexGenerationError,
    CodexLocalizationCancelled,
    generate_missing_localizations,
)
from codex_localization_runner import (
    CodexLocalizationError,
    check_codex_login_cancellable,
    run_codex_batch_cancellable,
)


ACTIVE_GENERATION_STATUSES = frozenset(("starting", "generating", "stopping"))
TERMINAL_GENERATION_STATUSES = frozenset(("completed", "failed", "stopped"))

_DEFAULT_CONTROLLER = None
_DEFAULT_CONTROLLER_LOCK = threading.Lock()


class DuplicateGenerationError(RuntimeError):
    """Raised when one owner already has a running generation job."""


@dataclass(frozen=True)
class GenerationEvent:
    job_id: str
    video_id: str
    kind: str
    index: int = 0
    total: int = 0
    codes: Tuple[str, ...] = ()
    batch_document: Mapping[str, Any] = None
    cumulative_document: Mapping[str, Any] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class GenerationSnapshot:
    job_id: str
    video_id: str
    target_codes: Tuple[str, ...]
    source_codes: Tuple[str, ...]
    status: str
    current_batch_index: int = 0
    total_batches: int = 0
    current_batch_codes: Tuple[str, ...] = ()
    completed_codes: Tuple[str, ...] = ()
    error: Optional[str] = None
    stop_requested: bool = False


class _GenerationRuntime:
    def __init__(
        self,
        owner_id: str,
        job_id: str,
        video_resource: Mapping[str, Any],
        catalog: Any,
        target_codes: Sequence[str],
        source_codes: Sequence[str],
    ) -> None:
        self.owner_id = owner_id
        self.job_id = job_id
        self.video_id = str(video_resource.get("id") or "")
        self.video_resource = copy.deepcopy(video_resource)
        self.catalog = copy.deepcopy(catalog)
        self.target_codes = tuple(target_codes)
        self.source_codes = tuple(source_codes)
        self.status = "starting"
        self.current_batch_index = 0
        self.total_batches = 0
        self.current_batch_codes = ()
        self.completed_codes = []
        self.error = None
        self.stop_requested = False
        self.events: Deque[GenerationEvent] = deque()
        self.cancel_event = threading.Event()
        self.lock = threading.RLock()
        self.thread = None

    def snapshot(self) -> GenerationSnapshot:
        with self.lock:
            return GenerationSnapshot(
                job_id=self.job_id,
                video_id=self.video_id,
                target_codes=self.target_codes,
                source_codes=self.source_codes,
                status=self.status,
                current_batch_index=self.current_batch_index,
                total_batches=self.total_batches,
                current_batch_codes=tuple(self.current_batch_codes),
                completed_codes=tuple(self.completed_codes),
                error=self.error,
                stop_requested=self.stop_requested,
            )


class GenerationController:
    """Own one background generation worker per Streamlit session owner."""

    DuplicateGenerationError = DuplicateGenerationError

    def __init__(
        self,
        *,
        generator: Callable[..., Mapping[str, Any]] = generate_missing_localizations,
        login_checker: Callable[[threading.Event], None] = check_codex_login_cancellable,
        runner: Callable[..., Mapping[str, Any]] = run_codex_batch_cancellable,
    ) -> None:
        self._generator = generator
        self._login_checker = login_checker
        self._runner = runner
        self._jobs = {}
        self._jobs_lock = threading.RLock()

    def start(
        self,
        owner_id: str,
        video_resource: Mapping[str, Any],
        catalog: Any,
        target_codes: Sequence[str],
        source_codes: Sequence[str] = (),
    ) -> GenerationSnapshot:
        if not owner_id:
            raise ValueError("generation owner id is required")
        with self._jobs_lock:
            current = self._jobs.get(owner_id)
            if current is not None and current.snapshot().status in ACTIVE_GENERATION_STATUSES:
                raise DuplicateGenerationError(
                    "A generation job is already active for this translation context."
                )

            job = _GenerationRuntime(
                owner_id,
                uuid.uuid4().hex,
                video_resource,
                catalog,
                tuple(target_codes),
                tuple(source_codes),
            )
            self._jobs[owner_id] = job
            job.thread = threading.Thread(
                target=self._run_job,
                args=(job,),
                name="youtube-codex-{}".format(job.job_id[:8]),
                daemon=True,
            )
            job.thread.start()
            return job.snapshot()

    def stop(self, owner_id: str, job_id: Optional[str] = None) -> bool:
        job = self._get_job(owner_id, job_id)
        if job is None:
            return False
        with job.lock:
            if job.status not in {"starting", "generating"}:
                return False
            job.status = "stopping"
            job.stop_requested = True
            job.cancel_event.set()
            return True

    def poll(
        self, owner_id: str, job_id: Optional[str] = None
    ) -> Tuple[Optional[GenerationSnapshot], Tuple[GenerationEvent, ...]]:
        job = self._get_job(owner_id, job_id)
        if job is None:
            return None, ()
        with job.lock:
            events = tuple(job.events)
            job.events.clear()
            return job.snapshot(), events

    def cleanup(self, owner_id: str, job_id: str) -> None:
        with self._jobs_lock:
            job = self._jobs.get(owner_id)
            if job is not None and job.job_id == job_id:
                with job.lock:
                    if job.status in TERMINAL_GENERATION_STATUSES and not job.thread.is_alive():
                        del self._jobs[owner_id]

    def active(self, owner_id: str, job_id: Optional[str] = None) -> bool:
        job = self._get_job(owner_id, job_id)
        return bool(job is not None and job.snapshot().status in ACTIVE_GENERATION_STATUSES)

    def _get_job(self, owner_id: str, job_id: Optional[str]):
        with self._jobs_lock:
            job = self._jobs.get(owner_id)
        if job is None or (job_id is not None and job.job_id != job_id):
            return None
        return job

    def _run_job(self, job: _GenerationRuntime) -> None:
        try:
            self._login_checker(job.cancel_event)
            with job.lock:
                if job.cancel_event.is_set():
                    raise CodexLocalizationCancelled("Generation stopped.")
                job.status = "generating"

            def run_batch(package, schema):
                return self._runner(
                    package,
                    schema,
                    cancel_event=job.cancel_event,
                )

            def on_batch(index, total, codes):
                with job.lock:
                    if job.cancel_event.is_set() or job.status == "stopping":
                        raise CodexLocalizationCancelled("Generation stopped.")
                    job.current_batch_index = index
                    job.total_batches = total
                    job.current_batch_codes = tuple(codes)

            def on_batch_completed(index, total, codes, batch_document, cumulative_document):
                with job.lock:
                    if job.cancel_event.is_set() or job.status == "stopping":
                        raise CodexLocalizationCancelled("Generation stopped.")
                    for code in codes:
                        if code.casefold() not in {
                            completed.casefold() for completed in job.completed_codes
                        }:
                            job.completed_codes.append(code)
                    job.events.append(
                        GenerationEvent(
                            job_id=job.job_id,
                            video_id=job.video_id,
                            kind="batch_completed",
                            index=index,
                            total=total,
                            codes=tuple(codes),
                            batch_document=copy.deepcopy(batch_document),
                            cumulative_document=copy.deepcopy(cumulative_document),
                        )
                    )

            self._generator(
                job.video_resource,
                job.catalog,
                target_codes=job.target_codes,
                selected_source_codes=job.source_codes,
                run_batch=run_batch,
                on_batch=on_batch,
                on_batch_completed=on_batch_completed,
            )
            self._finish(job, "completed")
        except CodexLocalizationCancelled:
            self._finish(job, "stopped")
        except (CodexGenerationError, CodexLocalizationError) as error:
            if job.cancel_event.is_set():
                self._finish(job, "stopped")
            else:
                self._finish(job, "failed", str(error))
        except Exception as error:
            if job.cancel_event.is_set():
                self._finish(job, "stopped")
            else:
                self._finish(job, "failed", str(error))

    def _finish(self, job: _GenerationRuntime, status: str, error: Optional[str] = None) -> None:
        with job.lock:
            if job.status in TERMINAL_GENERATION_STATUSES:
                return
            if job.stop_requested or job.cancel_event.is_set():
                status = "stopped"
                error = None
            job.status = status
            job.error = error
            job.events.append(
                GenerationEvent(
                    job_id=job.job_id,
                    video_id=job.video_id,
                    kind="terminal",
                    error=error,
                )
            )


def get_generation_controller() -> GenerationController:
    """Return the process-local controller used by the Streamlit session."""
    global _DEFAULT_CONTROLLER
    with _DEFAULT_CONTROLLER_LOCK:
        if _DEFAULT_CONTROLLER is None:
            _DEFAULT_CONTROLLER = GenerationController()
        return _DEFAULT_CONTROLLER
