import os
from dotenv import load_dotenv
import deepl.exceptions
import googleapiclient
from deepl import Translator
from flask import Flask, request, render_template, jsonify, redirect, url_for

from google_translate import TranslateApi
from youtube_account import YoutubeApi

import time

# Configuration
DEBUG = True

# Instantiate the app
load_dotenv()
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

language_names_added = False


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


def do_translations(selected_videos, selected_languages, overwrite, use_deepl, trim_checked):
    """Perform translations for selected videos and languages"""
    youtube_api.videos_skipped = 0
    youtube_api.videos_trimmed = 0
    youtube_api.errorStr = ''
    
    # Use the full cache if "ALL" videos were selected for translation
    videos_to_search = youtube_api.all_videos_cache if youtube_api.results_per_page == -1 else youtube_api.page_videos

    for video_title in selected_videos:
        target_video = None
        for video in videos_to_search:
            if str(video.video_title).replace(' ', '') == str(video_title).replace(' ', ''):
                target_video = video
                break
                
        if not target_video:
            print(f"Video '{video_title}' not found in current context")
            continue

        for language in selected_languages:
            if language in target_video.language_names and not overwrite:
                continue
                
            language_code = youtube_api.name_to_code.get(language.strip(), '')
            if not language_code:
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
                    translated_title = translate_api.translate_text(language_code, target_video.video_title)
                    translated_desc = translate_api.translate_text(language_code, target_video.description)
                    translated = True
                else:
                    print(f"Language code '{language_code}' not available")

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
    global language_names_added
    
    try:
        if request.method == 'POST':
            youtube_api.errorStr = ''
            json_data = request.get_json()

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
                language_names_added = False # Forzar a que se recalculen los nombres
                return jsonify({"status": "ok"})
        
        # Para peticiones GET
        page = request.args.get('page', 1, type=int)
        
        # Cargar los vídeos para la página actual (solo si la caché está vacía)
        youtube_api.set_video_page(page)
        set_language_names()
        
        if youtube_api.errorStr == 'quotaExceeded':
            return render_template("quota-error.html")
            
        all_video_titles = [vid.video_title for vid in youtube_api.all_videos_cache] if youtube_api.results_per_page == -1 else []
        
        return render_template(
            'home.html', 
            page_videos=youtube_api.page_videos,
            all_videos=all_video_titles,
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


@app.route("/languages", methods=['POST'])
def get_current_languages():
    """API endpoint to get languages that are common to ALL selected videos"""
    try:
        num_selected = request.json.get('num', 0)
        selected_video_names = [name.replace(' ', '') for name in request.json.get('vidNames', [])]
        
        results = {}
        
        videos_to_check = youtube_api.all_videos_cache if youtube_api.results_per_page == -1 else youtube_api.page_videos
        
        for video in videos_to_check:
            if video.video_title.replace(' ', '') in selected_video_names:
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
    global language_names_added
    
    if not language_names_added:
        videos_to_process = youtube_api.page_videos
        for video in videos_to_process:
            video.language_names = []
            for lang_code in video.current_languages:
                language_name = youtube_api.code_to_name.get(lang_code, '')
                if language_name and language_name not in video.language_names:
                    video.language_names.append(language_name)
        language_names_added = True


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)