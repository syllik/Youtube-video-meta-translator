"""Generate missing YouTube localization JSON through local Codex CLI."""

import argparse
import sys
from pathlib import Path

from codex_localization_generator import (
    generate_missing_localizations,
    write_localizations_atomic,
)
from codex_localization_runner import check_codex_login, run_codex_batch
from llm_localization_package import LLM_BATCH_SIZE
from services.youtube_service import YoutubeService


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Generate currently missing YouTube localization JSON "
            "with the locally authenticated Codex CLI."
        )
    )
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--batch-size", type=int, default=LLM_BATCH_SIZE)
    parser.add_argument("--max-languages", type=int)
    parser.add_argument("--output", type=Path, default=Path("localizations.json"))
    return parser


def main(
    argv=None,
    *,
    service_factory=YoutubeService,
    login_checker=check_codex_login,
    run_batch=run_codex_batch,
):
    args = build_parser().parse_args(argv)

    try:
        if args.batch_size < 1 or args.batch_size > LLM_BATCH_SIZE:
            raise ValueError(
                "--batch-size must be between 1 and {}".format(LLM_BATCH_SIZE)
            )
        if args.max_languages is not None and args.max_languages < 1:
            raise ValueError("--max-languages must be positive")

        login_checker()
        service = service_factory()
        video_resource = service.get_video_with_localizations(args.video_id)
        catalog = service.fetch_localization_language_catalog(
            hl="ru", refresh=True
        )

        def report_batch(index, total, codes):
            print(
                "Codex batch {}/{}: {}".format(
                    index, total, ", ".join(codes)
                )
            )

        result = generate_missing_localizations(
            video_resource,
            catalog,
            batch_size=args.batch_size,
            max_languages=args.max_languages,
            run_batch=run_batch,
            on_batch=report_batch,
        )

        if not result:
            print("No missing supported YouTube localizations.")
            return 0

        write_localizations_atomic(result, args.output)
    except Exception as error:
        print(
            "Localization generation failed: {}".format(error),
            file=sys.stderr,
        )
        return 1

    print("Generated {} localizations -> {}".format(len(result), args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
