import html
import os
import pickle

import google_auth_oauthlib
import googleapiclient.errors
import google.auth.exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# YouTube API configuration
scopes = ["https://www.googleapis.com/auth/youtube"]
api_service_name = "youtube"
api_version = "v3"
TOKEN_FILE = "token.json"
LEGACY_TOKEN_FILE = "token.pickle"


class YoutubeVideoNotFoundError(ValueError):
    """Raised when a requested video id has no unique YouTube resource."""


class _RestrictedCredentialUnpickler(pickle.Unpickler):
    """Load only the OAuth credential class from the legacy token cache."""

    _allowed_globals = {
        ("google.oauth2.credentials", "Credentials"): Credentials,
    }

    def find_class(self, module, name):
        try:
            return self._allowed_globals[(module, name)]
        except KeyError:
            raise pickle.UnpicklingError(
                "Legacy token contains an unsupported serialized object"
            ) from None


def _load_legacy_credentials(token_file):
    credentials = _RestrictedCredentialUnpickler(token_file).load()
    if not isinstance(credentials, Credentials):
        raise pickle.UnpicklingError(
            "Legacy token does not contain OAuth credentials"
        )
    return credentials


def _http_error_reason(error, fallback="youtubeApiError"):
    details = getattr(error, "error_details", None) or []
    if details and isinstance(details[0], dict):
        return details[0].get("reason") or fallback
    return fallback


class YoutubeApi:
    def __init__(self):
        self.credentials = None
        self.page_videos = []
        self.all_videos_cache = []  # Cache for when ALL option is selected
        self.youtube = None
        self.channel_thumbnail = ''
        self.channel_name = ''
        self.uploads_id = ''
        self.next_page_token = None
        self.page_tokens = {}  # Store page tokens for efficient pagination
        self.results_per_page = 10
        self.per_page_option_index = 0
        self.current_page = 1
        self.videos_trimmed = 0
        self.videos_skipped = 0
        self.errorStr = ''
        self.total_video_count = 0
        self.allowed_languages = []
        self.localization_read_errors = set()
        
        self.code_to_name = {
            "af": "Afrikaans",
            "am": "Amharic",
            "ar": "Arabic",
            "az": "Azerbaijani",
            "be": "Belarusian",
            "bg": "Bulgarian",
            "bn": "Bangla",        
            "bs": "Bosnian",
            "ca": "Catalan",
            "cs": "Czech",
            "da": "Danish",
            "de": "German",
            "en": "English",
            "es": "Spanish",
            "et": "Estonian",
            "eu": "Basque",
            "fa": "Persian",
            "fi": "Finnish",
            "fr": "French",
            "gl": "Galician",
            "gu": "Gujarati",
            "hi": "Hindi",
            "hr": "Croatian",
            "hu": "Hungarian",
            "hy": "Armenian",
            "id": "Indonesian",
            "is": "Icelandic",
            "it": "Italian",
            "iw": "Hebrew",
            "ja": "Japanese",
            "ka": "Georgian",
            "kk": "Kazakh",
            "km": "Khmer",
            "kn": "Kannada",
            "ko": "Korean",
            "ky": "Kyrgyz",
            "lo": "Lao",
            "lt": "Lithuanian",
            "lv": "Latvian",
            "mk": "Macedonian",
            "ml": "Malayalam",
            "mn": "Mongolian",
            "mr": "Marathi",
            "ms": "Malay",
            "my": "Burmese",
            "no": "Norwegian",
            "ne": "Nepali",
            "nl": "Dutch",
            "or": "Odia",
            "pa": "Punjabi",
            "pl": "Polish",
            "pt": "Portuguese",
            "ro": "Romanian",
            "ru": "Russian",
            "si": "Sinhala",
            "sk": "Slovak",
            "sl": "Slovenian",
            "sq": "Albanian",
            "sr": "Serbian",
            "sv": "Swedish",
            "sw": "Swahili",
            "ta": "Tamil",
            "te": "Telugu",
            "th": "Thai",
            "tr": "Turkish",
            "uk": "Ukrainian",
            "ur": "Urdu",
            "vi": "Vietnamese",
            "zh-CN": "Chinese (China)",
            "zh-TW": "Chinese (Taiwan)",
        }
        self.name_to_code = {val: key for (key, val) in self.code_to_name.items()}
        
        self.check_credentials()
        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=self.credentials)
        self.set_uploads_id()
        if self.errorStr == '':
            self.get_total_video_count()
            # We don't need to load the page here, home() will do it.
            # self.set_video_page(1)

    @property
    def num_pages(self):
        if self.results_per_page == -1:  # "ALL" option
            return 1
        return max(1, (self.total_video_count + self.results_per_page - 1) // self.results_per_page)

    def check_credentials(self):
        """Check and refresh OAuth credentials"""
        credentials_need_save = False

        if os.path.exists(TOKEN_FILE):
            try:
                os.chmod(TOKEN_FILE, 0o600)
                self.credentials = Credentials.from_authorized_user_file(
                    TOKEN_FILE, scopes=scopes
                )
            except (OSError, TypeError, ValueError):
                self.credentials = None

        if self.credentials is None and os.path.exists(LEGACY_TOKEN_FILE):
            try:
                os.chmod(LEGACY_TOKEN_FILE, 0o600)
                with open(LEGACY_TOKEN_FILE, "rb") as token:
                    self.credentials = _load_legacy_credentials(token)
                credentials_need_save = True
            except (
                AttributeError,
                EOFError,
                ImportError,
                OSError,
                ValueError,
                pickle.UnpicklingError,
            ):
                self.credentials = None

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                    credentials_need_save = True
                except google.auth.exceptions.RefreshError:
                    self.credentials = None
            if not self.credentials:
                # Get credentials and create an API client
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file="config/account_client_secrets_main.json", scopes=scopes)
                previous_transport_setting = os.environ.get("OAUTHLIB_INSECURE_TRANSPORT")
                os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
                try:
                    flow.run_local_server(port=8080, prompt='consent', authorization_prompt_message='')
                finally:
                    if previous_transport_setting is None:
                        os.environ.pop("OAUTHLIB_INSECURE_TRANSPORT", None)
                    else:
                        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = previous_transport_setting
                self.credentials = flow.credentials
                credentials_need_save = True

        if credentials_need_save:
            with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
                token_file.write(self.credentials.to_json())
            os.chmod(TOKEN_FILE, 0o600)

    # --- NUEVO MÉTODO AÑADIDO ---
    def clear_video_cache(self):
        """Clears all in-memory video data to force a re-fetch on the next page load."""
        self.page_videos = []
        self.all_videos_cache = []
        self.page_tokens = {} # Important to reset this as well
        self.localization_read_errors.clear()
        print("In-memory video cache cleared.")
    # --- FIN DEL NUEVO MÉTODO ---

    def set_channel_data(self, channel_response):
        """Extract channel information from API response"""
        if channel_response.get("items"):
            self.channel_thumbnail = channel_response["items"][0]['snippet']['thumbnails']['default']['url']
            self.channel_name = channel_response["items"][0]['snippet']['title']

    def get_total_video_count(self):
        """Get total number of videos in channel without fetching all video details"""
        try:
            playlist_response = self.youtube.playlists().list(
                id=self.uploads_id,
                part='contentDetails'
            ).execute()
            
            if playlist_response.get("items"):
                self.total_video_count = playlist_response["items"][0]["contentDetails"]["itemCount"]
            else:
                response = self.youtube.playlistItems().list(
                    playlistId=self.uploads_id,
                    part='id',
                    maxResults=1
                ).execute()
                self.total_video_count = response.get('pageInfo', {}).get('totalResults', 0)
                
        except googleapiclient.errors.HttpError as e:
            self.errorStr = e.error_details[0]['reason']
            self.total_video_count = 0

    def set_video_page(self, page):
        """Load videos for a specific page on demand"""
        # A page cache belongs to one page. Keep the existing cache behavior
        # for repeated requests, but do not show the previous page after
        # navigation.
        if self.results_per_page != -1 and self.current_page != page:
            self.page_videos = []

        if not self.page_videos:
            self.current_page = page
            if self.results_per_page == -1:  # "ALL" option
                self.load_all_videos()
            else:
                self.load_page_videos(page)

    def load_page_videos(self, page):
        """Load videos for a specific page efficiently"""
        try:
            page_token = self.get_page_token_for_page(page)
            
            videos_response = self.youtube.playlistItems().list(
                playlistId=self.uploads_id,
                part='snippet',
                maxResults=self.results_per_page,
                pageToken=page_token
            ).execute()

            if videos_response.get("nextPageToken"):
                self.page_tokens[page + 1] = videos_response["nextPageToken"]

            for item in videos_response["items"]:
                video_id = item["snippet"]["resourceId"]["videoId"]
                localizations = self.get_video_localizations(video_id)
                
                new_video = Video(
                    item["snippet"]["title"], 
                    video_id, 
                    item["snippet"]["description"],
                    item["snippet"]["thumbnails"]["default"]['url'], 
                    localizations
                )
                self.page_videos.append(new_video)
                
        except googleapiclient.errors.HttpError as e:
            self.errorStr = e.error_details[0]['reason']

    def get_page_token_for_page(self, page):
        """Get the appropriate page token for a given page number"""
        if page == 1:
            return None
            
        if page in self.page_tokens:
            return self.page_tokens[page]
            
        current_page = 1
        page_token = None
        
        while current_page < page:
            response = self.youtube.playlistItems().list(
                playlistId=self.uploads_id,
                part='id',
                maxResults=self.results_per_page,
                pageToken=page_token
            ).execute()
            
            page_token = response.get("nextPageToken")
            current_page += 1
            
            if page_token:
                self.page_tokens[current_page] = page_token
            else:
                break
                
        return page_token

    def load_all_videos(self):
        """Load all videos when 'ALL' option is selected"""
        self.page_videos = []
        self.all_videos_cache = []
        page_token = None
        
        try:
            while True:
                videos_response = self.youtube.playlistItems().list(
                    playlistId=self.uploads_id,
                    part='snippet',
                    maxResults=50,
                    pageToken=page_token
                ).execute()

                for item in videos_response["items"]:
                    video_id = item["snippet"]["resourceId"]["videoId"]
                    localizations = self.get_video_localizations(video_id)
                    
                    new_video = Video(
                        item["snippet"]["title"], 
                        video_id, 
                        item["snippet"]["description"],
                        item["snippet"]["thumbnails"]["default"]['url'], 
                        localizations
                    )
                    self.page_videos.append(new_video)
                    self.all_videos_cache.append(new_video)

                page_token = videos_response.get("nextPageToken")
                if not page_token:
                    break
                    
        except googleapiclient.errors.HttpError as e:
            self.errorStr = e.error_details[0]['reason']

    def set_uploads_id(self):
        """Get the uploads playlist ID for the authenticated channel"""
        try:
            channel_response = self.youtube.channels().list(
                part="snippet",
                mine=True
            ).execute()
            self.set_channel_data(channel_response)
            channel_id = channel_response["items"][0]["id"]
            uploads_response = self.youtube.channels().list(
                id=channel_id,
                part='contentDetails'
            ).execute()
            self.uploads_id = uploads_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        except googleapiclient.errors.HttpError as e:
            self.errorStr = e.error_details[0]['reason']

    def set_video_localization(self, video_id, language_code, language, title, description, trim_checked,
                               default_title):
        """Add or update localization for a video"""
        if language_code == '':
            return
            
        video = {}
        language = language.strip()
        print(f"Translating '{default_title}' to '{language}'")
        
        if trim_checked:
            if len(title) > 99:
                title = title[:98]
                self.videos_trimmed += 1
                print(f"Title for video '{default_title}' was too long, trimmed")
            if len(description) > 4999:
                description = description[:4998]
                self.videos_trimmed += 1
                print(f"Description for video '{default_title}' was too long, trimmed")
        else:
            if len(title) > 99 or len(description) > 4999:
                self.videos_skipped += 1
                print(f"Video '{default_title}' skipped for language '{language}' due to length.")
                return
                
        try:
            results = self.youtube.videos().list(
                part='snippet,localizations',
                id=video_id
            ).execute()
            
            video = results['items'][0]
            
            if not video['snippet'].get('defaultLanguage'):
                self.errorStr = 'defaultLanguageNotSet'
                print(f"Video '{default_title}' has no default language")
                return
                
            if 'localizations' not in video:
                video['localizations'] = {}
                
            video['localizations'][language_code] = {
                'title': html.unescape(title.replace('\\n', '\n')),
                'description': html.unescape(description.replace('\\n', '\n'))
            }
            
            self.youtube.videos().update(
                part='snippet,localizations',
                body=video
            ).execute()
            
        except googleapiclient.errors.HttpError as e:
            self.errorStr = e.error_details[0]['reason']
            print(f"Error updating video: {e.error_details}")

    def get_video_with_localizations(self, video_id):
        """Fetch one complete video resource for preview or publishing."""
        results = self.youtube.videos().list(
            part='snippet,localizations',
            id=video_id
        ).execute()
        items = results.get('items', [])
        if len(items) != 1:
            raise YoutubeVideoNotFoundError(
                "YouTube returned no unique video for the requested id"
            )
        return items[0]

    def update_video_localizations(self, payload):
        """Publish one already-merged localization update."""
        return self.youtube.videos().update(
            part='snippet,localizations',
            body=payload
        ).execute()

    def get_video_localizations(self, video_id):
        """Get existing localizations for a video"""
        try:
            results = self.youtube.videos().list(
                part='localizations',
                id=video_id
            ).execute()
            
            if not results['items']:
                return []
            
            localizations = list(results['items'][0].get('localizations', {}).keys())

            return list(dict.fromkeys(localizations))
            
        except googleapiclient.errors.HttpError as e:
            print(f"Error getting localizations for video {video_id}: {e}")
            self.errorStr = _http_error_reason(e)
            self.localization_read_errors = getattr(
                self, "localization_read_errors", set()
            )
            self.localization_read_errors.add(str(video_id))
            return []


class Video:
    """Represents a YouTube video with translation data"""
    
    def __init__(self, title, vid_id, desc, thumb_url, curr_langs):
        self.video_title = title
        self.id = vid_id
        self.description = desc
        self.thumbnail_url = thumb_url
        self.current_languages = curr_langs if curr_langs else []
        self.language_names = []

    @property
    def num_languages(self):
        return len(self.current_languages)
