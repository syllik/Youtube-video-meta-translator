import json
import os
from dotenv import load_dotenv
import deepl.exceptions
import googleapiclient
from deepl import Translator
from flask import Flask, request, render_template, jsonify, redirect, url_for

from google_translate import TranslateApi, TranslationError
from localization_service import preview_localizations, publish_localizations
from youtube_account import YoutubeApi, YoutubeVideoNotFoundError

import time

# Load local configuration before evaluating settings derived from it.
load_dotenv()

# Configuration
DEBUG = os.getenv('FLASK_DEBUG', '').strip().lower() in {'1', 'true', 'yes', 'on'}

# Instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Initialize APIs
youtube_api = YoutubeApi()
translate_api = TranslateApi()

# Initialize DeepL translator if API key is available
deepl_translator = None
deepl_api_key = os.getenv('DEEPL_API_KEY')
if deepl_api_key:
    try:
        deepl_translator = Translator(deepl_api_key)
    except Exception as e:
        print(f"Failed to initialize DeepL translator: {e}")
        deepl_translator = None

def check_translation(video_id, language_code):
    """Check if a translation already exists for a video"""
    try:
        video_info = youtube_api.youtube.videos().list(
            part='localizations',
            id=video_id
        ).execute()

        if 'localizations' in video_info['items'][0]:
            if language_code in video_info['items'][0]['localizations']:
                return True
    except Exception as e:
        print(f"Error checking translation: {e}")
        
    return False


def _find_legacy_video(videos, reference):
    reference = str(reference)
    id_matches = [
        video for video in videos if str(video.id) == reference
    ]
    if len(id_matches) == 1:
        return id_matches[0], None

    normalized_reference = reference.replace(' ', '')
    title_matches = [
        video for video in videos
        if str(video.video_title).replace(' ', '') == normalized_reference
    ]
    if len(title_matches) == 1:
        return title_matches[0], None
    if len(title_matches) > 1:
        return None, 'videoAmbiguous'
    return None, 'videoNotFound'


def do_translations(selected_videos, selected_languages, overwrite, use_deepl, trim_checked):
    """Perform translations for selected videos and languages"""
    youtube_api.videos_skipped = 0
    youtube_api.videos_trimmed = 0
    youtube_api.errorStr = ''
    
    # Use the full cache if "ALL" videos were selected for translation
    videos_to_search = youtube_api.all_videos_cache if youtube_api.results_per_page == -1 else youtube_api.page_videos

    for video_id in selected_videos:
        target_video, lookup_error = _find_legacy_video(videos_to_search, video_id)

        if not target_video:
            youtube_api.errorStr = lookup_error
            print(f"Video reference '{video_id}' could not be resolved ({lookup_error})")
            return

        if str(target_video.id) in getattr(
            youtube_api, 'localization_read_errors', set()
        ):
            youtube_api.errorStr = 'localizationReadFailed'
            print(f"Current localizations for video '{target_video.id}' are unavailable")
            return

        for language in selected_languages:
            language_code = youtube_api.name_to_code.get(language.strip(), '')
            if not language_code:
                youtube_api.errorStr = 'translationUnavailable'
                print(f"Language '{language}' is not available")
                return

            if (
                not overwrite
                and language_code in getattr(target_video, 'current_languages', [])
            ):
                continue
                
            translated = False
            translated_title, translated_desc = '', ''
            
            if use_deepl and deepl_translator:
                try:
                    available_deepl = [x.code.lower() for x in deepl_translator.get_target_languages()]
                    if language_code in available_deepl:
                        translated_title = deepl_translator.translate_text(target_video.video_title, target_lang=language_code).text
                        translated_desc = deepl_translator.translate_text(target_video.description, target_lang=language_code).text
                        translated = True
                except deepl.exceptions.QuotaExceededException:
                    print(f"DeepL quota exceeded, falling back to Google Translate")
                except Exception as e:
                    print(f"DeepL error: {e}, falling back to Google Translate")
            
            if not translated:
                if language_code in translate_api.all_language_codes:
                    try:
                        translated_title = translate_api.translate_text(language_code, target_video.video_title)
                        translated_desc = translate_api.translate_text(language_code, target_video.description)
                        translated = True
                    except TranslationError as e:
                        youtube_api.errorStr = 'translationFailed'
                        print(f"Google Translate error: {e}")
                        return
                else:
                    youtube_api.errorStr = 'translationUnavailable'
                    print(f"Language code '{language_code}' not available")
                    return

            if translated:
                youtube_api.set_video_localization(
                    target_video.id, language_code, language, 
                    translated_title, translated_desc, trim_checked, target_video.video_title
                )
                time.sleep(1) # Small delay between API calls

            if youtube_api.errorStr:
                return


@app.route('/', methods=['GET', 'POST'])
def home():
    """Main route handling both page display and AJAX requests"""
    try:
        if request.method == 'POST':
            youtube_api.errorStr = ''
            json_data = request.get_json(silent=True)
            if not isinstance(json_data, dict):
                return jsonify({
                    'status': 'error',
                    'error_type': 'invalidRequest',
                    'error': 'Request body must be a JSON object.',
                }), 400

            if 'per_page' in json_data:
                page = 1
                per_page = int(json_data['per_page'])
                youtube_api.per_page_option_index = int(json_data.get('per_page_option_index', 0))
                
                youtube_api.results_per_page = per_page if per_page < youtube_api.total_video_count else -1
                youtube_api.clear_video_cache()
                return redirect(url_for('home', page=1))
            
            if 'selected_videos' in json_data and 'selected_languages' in json_data:
                do_translations(
                    json_data['selected_videos'], 
                    json_data['selected_languages'],
                    json_data.get('overwrite', False), 
                    json_data.get('use_deepL', False), 
                    json_data.get('trim_checked', False)
                )
                # --- LÍNEA CLAVE AÑADIDA ---
                # Después de traducir, la caché en memoria es obsoleta. La borramos.
                youtube_api.clear_video_cache()
                if youtube_api.errorStr:
                    return _legacy_error_response()
                return jsonify({"status": "ok"})
        
        # Para peticiones GET
        page = request.args.get('page', 1, type=int)
        
        # Cargar los vídeos para la página actual (solo si la caché está vacía)
        youtube_api.set_video_page(page)
        set_language_names()
        
        if youtube_api.errorStr == 'quotaExceeded':
            return render_template("quota-error.html")
            
        all_video_entries = [
            {'id': vid.id, 'title': vid.video_title}
            for vid in youtube_api.all_videos_cache
        ] if youtube_api.results_per_page == -1 else []
        
        return render_template(
            'home.html', 
            page_videos=youtube_api.page_videos,
            all_videos=all_video_entries,
            all_language_names=list(youtube_api.name_to_code.keys()),
            channel_thumbnail=youtube_api.channel_thumbnail, 
            channel_name=youtube_api.channel_name,
            num_pages=youtube_api.num_pages + 1, 
            current_page=page,
            error_str=youtube_api.errorStr, 
            per_page_index=youtube_api.per_page_option_index,
            trimmed=youtube_api.videos_trimmed, 
            skipped=youtube_api.videos_skipped,
            total_videos=youtube_api.total_video_count
        )
        
    except (googleapiclient.errors.HttpError, IndexError) as e:
        print(f"Error in home route: {e}")
        return render_template("quota-error.html")


@app.route("/error/", methods=['GET'])
def get_error():
    """API endpoint to get current error status"""
    return jsonify({
        'error': youtube_api.errorStr,
        'trimmed': youtube_api.videos_trimmed,
        'skipped': youtube_api.videos_skipped
    })


def _legacy_error_response():
    error_code = youtube_api.errorStr or 'translationFailed'
    messages = {
        'defaultLanguageNotSet': 'Set the original video language in YouTube before translating.',
        'quotaExceeded': 'YouTube API quota exceeded. Please try again later.',
        'translationFailed': 'Translation provider failed. No localization was published.',
        'translationUnavailable': 'The selected translation language is unavailable.',
        'localizationReadFailed': 'Could not read current localizations. No localization was published.',
        'videoNotFound': 'The selected video was not found in the current list.',
        'videoAmbiguous': 'The selected video title matches more than one video. Select it again using its ID.',
    }
    if error_code == 'videoAmbiguous':
        status = 409
    else:
        status = 429 if error_code == 'quotaExceeded' else 502
    return jsonify({
        'status': 'error',
        'error_type': error_code,
        'error': messages.get(error_code, 'The translation could not be published.'),
    }), status


@app.route("/languages", methods=['POST'])
def get_current_languages():
    """API endpoint to get languages that are common to ALL selected videos"""
    try:
        data = request.get_json(silent=True) or {}
        num_selected = data.get('num', 0)
        selected_video_ids = {
            str(video_id) for video_id in data.get('vidIds', [])
        }
        selected_video_names = [
            str(name).replace(' ', '') for name in data.get('vidNames', [])
        ]

        videos_to_check = youtube_api.all_videos_cache if youtube_api.results_per_page == -1 else youtube_api.page_videos

        if not selected_video_ids and selected_video_names:
            resolved_ids = set()
            for selected_name in selected_video_names:
                matches = [
                    video for video in videos_to_check
                    if str(video.video_title).replace(' ', '') == selected_name
                ]
                if len(matches) > 1:
                    return jsonify({
                        'status': 'error',
                        'error_type': 'videoAmbiguous',
                        'error': (
                            'The selected video title matches more than one video. '
                            'Select it again using its ID.'
                        ),
                    }), 409
                if len(matches) == 1:
                    resolved_ids.add(str(matches[0].id))
            selected_video_ids = resolved_ids
        
        results = {}
        
        for video in videos_to_check:
            is_selected = (
                str(video.id) in selected_video_ids
                if selected_video_ids
                else str(video.video_title).replace(' ', '') in selected_video_names
            )
            if is_selected:
                for lang in video.language_names:
                    if lang not in results:
                        results[lang] = 1
                    else:
                        results[lang] += 1
        
        langs = [lang for lang, count in results.items() if count == num_selected]
        return jsonify({'current_languages': langs})
        
    except Exception as e:
        print(f"Error in get_current_languages: {e}")
        return jsonify({'current_languages': []})


def set_language_names():
    """Convert language codes to human-readable names for display"""
    for video in youtube_api.page_videos:
        video.language_names = []
        for lang_code in video.current_languages:
            language_name = youtube_api.code_to_name.get(lang_code, '')
            if not language_name and isinstance(lang_code, str) and '-' in lang_code:
                language_name = youtube_api.code_to_name.get(
                    lang_code.split('-', 1)[0], ''
                )
            if language_name and language_name not in video.language_names:
                video.language_names.append(language_name)


def _localization_request_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    video_id = data.get('video_id')
    if not isinstance(video_id, str) or not video_id.strip():
        raise ValueError("video_id must be a non-empty string")

    has_object = 'localizations' in data
    has_raw = 'localizations_json' in data
    if has_object and has_raw:
        raise ValueError("Provide either localizations or localizations_json, not both")
    if not has_object and not has_raw:
        raise ValueError("localizations or localizations_json is required")

    if has_raw:
        raw_json = data['localizations_json']
        if not isinstance(raw_json, str):
            raise ValueError("localizations_json must be a string")
    else:
        if not isinstance(data['localizations'], dict):
            raise ValueError("localizations must be a JSON object")
        raw_json = json.dumps(data['localizations'], ensure_ascii=False)

    return video_id.strip(), raw_json


def _supported_localization_codes():
    # Keep the existing language directory unchanged while accepting the
    # regional code used by the manual editor contract.
    return set(youtube_api.code_to_name.keys()) | {'pt-BR'}


def _localization_value_to_dict(value):
    return value.to_dict() if value is not None else None


def _serialize_localization_result(result, include_wrote=False):
    summary = {'added': 0, 'changed': 0, 'unchanged': 0}
    languages = []
    for diff in result.plan.diffs:
        summary[diff.status] += 1
        languages.append({
            'language': diff.language_code,
            'status': diff.status,
            'before': _localization_value_to_dict(diff.existing),
            'after': _localization_value_to_dict(diff.submitted),
        })

    response = {
        'valid': result.plan.is_valid,
        'summary': summary,
        'languages': languages,
        'errors': [
            {'path': issue.path, 'message': issue.message}
            for issue in result.plan.issues
        ],
        'preserved_language_codes': list(result.plan.preserved_language_codes),
    }
    if include_wrote:
        response['wrote'] = result.wrote
    return response


def _youtube_error_response(error):
    app.logger.exception("Localization API failed")
    reason = ''
    details = getattr(error, 'error_details', None) or []
    if details and isinstance(details[0], dict):
        reason = details[0].get('reason', '')

    if reason == 'quotaExceeded':
        return jsonify({
            'valid': False,
            'error_type': 'quota_exceeded',
            'error': 'YouTube API quota exceeded. Please try again later.',
        }), 429

    status = getattr(getattr(error, 'resp', None), 'status', None)
    if status == 404:
        return jsonify({
            'valid': False,
            'error_type': 'video_not_found',
            'error': 'The selected YouTube video was not found.',
        }), 404

    return jsonify({
        'valid': False,
        'error_type': 'youtube_api',
        'error': 'YouTube API request failed. Check the server log for details.',
    }), 502


def _run_localization_operation(operation, include_wrote):
    try:
        video_id, raw_json = _localization_request_data()
    except ValueError as error:
        return jsonify({'valid': False, 'error': str(error)}), 400

    try:
        result = operation(
            youtube_api,
            video_id,
            raw_json,
            _supported_localization_codes(),
        )
    except googleapiclient.errors.HttpError as error:
        return _youtube_error_response(error)
    except YoutubeVideoNotFoundError:
        return jsonify({
            'valid': False,
            'error_type': 'video_not_found',
            'error': 'The selected YouTube video was not found.',
        }), 404
    except Exception as error:
        return _youtube_error_response(error)

    response = _serialize_localization_result(result, include_wrote=include_wrote)
    return jsonify(response), 200 if result.plan.is_valid else 422


@app.route('/api/localizations/preview', methods=['POST'])
def localization_preview():
    """Validate and preview submitted localizations without writing."""
    return _run_localization_operation(preview_localizations, include_wrote=False)


@app.route('/api/localizations/publish', methods=['POST'])
def localization_publish():
    """Validate and publish one merged localization update."""
    return _run_localization_operation(publish_localizations, include_wrote=True)


if __name__ == '__main__':
    app.run(debug=DEBUG, host='127.0.0.1', port=5001)
