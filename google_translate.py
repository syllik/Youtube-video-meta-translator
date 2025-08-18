import os
import six
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError


class TranslateApi:
    """Google Cloud Translation API wrapper"""
    
    def __init__(self):
        self.all_languages = []
        self.all_language_names = []
        self.all_language_codes = []
        self.credentials = None
        self.translate_client = None
        
        self.initialize_client()
        if self.translate_client:
            self.initialize_all_languages()

    def initialize_client(self):
        """Initialize the Google Cloud Translation client"""
        try:
            # Try to load credentials from config file
            credentials_path = 'config/translate_key.json'
            if os.path.exists(credentials_path):
                self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.translate_client = translate.Client(credentials=self.credentials)
                print("Google Cloud Translation API initialized successfully")
            else:
                print(f"Warning: Credentials file not found at {credentials_path}")
                # Try to use default credentials (for deployed environments)
                try:
                    self.translate_client = translate.Client()
                    print("Using default Google Cloud credentials")
                except DefaultCredentialsError:
                    print("Error: No valid Google Cloud credentials found")
                    self.translate_client = None
                    
        except Exception as e:
            print(f"Error initializing Google Cloud Translation client: {e}")
            self.translate_client = None

    def initialize_all_languages(self):
        """Load all available languages from Google Translate API"""
        try:
            if not self.translate_client:
                print("Warning: Translation client not available, cannot load languages")
                return
                
            # Get all supported languages
            languages_response = self.translate_client.get_languages()
            self.all_languages = [lang for lang in languages_response]
            self.all_language_names = [lang['name'] for lang in self.all_languages]
            self.all_language_codes = [lang['language'] for lang in self.all_languages]
            
            print(f"Loaded {len(self.all_languages)} supported languages from Google Translate")
            
        except Exception as e:
            print(f"Error loading supported languages: {e}")
            self.all_languages = []
            self.all_language_names = []
            self.all_language_codes = []

    def translate_text(self, target_language, text):
        """
        Translate text to target language
        
        Args:
            target_language (str): Target language code (e.g., 'es', 'fr', 'de')
            text (str): Text to translate
            
        Returns:
            str: Translated text, or original text if translation fails
        """
        if not self.translate_client:
            print("Warning: Translation client not available")
            return text
            
        if not text or not text.strip():
            return text
            
        try:
            # Handle binary text
            if isinstance(text, six.binary_type):
                text = text.decode("utf-8")
            
            # Perform translation
            result = self.translate_client.translate(
                text, 
                format_='text', 
                target_language=target_language
            )
            
            translated_text = result.get("translatedText", text)
            
            # Log successful translation
            print(f"Translated to {target_language}: '{text[:50]}...' -> '{translated_text[:50]}...'")
            
            return translated_text
            
        except Exception as e:
            print(f"Error translating text to {target_language}: {e}")
            print(f"Original text: {text[:100]}...")
            return text  # Return original text if translation fails

    def is_language_supported(self, language_code):
        """
        Check if a language code is supported by Google Translate
        
        Args:
            language_code (str): Language code to check
            
        Returns:
            bool: True if language is supported, False otherwise
        """
        return language_code.lower() in [code.lower() for code in self.all_language_codes]

    def get_language_name(self, language_code):
        """
        Get the human-readable name for a language code
        
        Args:
            language_code (str): Language code
            
        Returns:
            str: Language name, or the code itself if not found
        """
        for lang in self.all_languages:
            if lang['language'].lower() == language_code.lower():
                return lang['name']
        return language_code

    def get_supported_languages_info(self):
        """
        Get information about all supported languages
        
        Returns:
            dict: Dictionary with language statistics and info
        """
        return {
            'total_languages': len(self.all_languages),
            'language_codes': self.all_language_codes,
            'language_names': self.all_language_names,
            'client_available': self.translate_client is not None
        }

    def batch_translate(self, target_language, texts):
        """
        Translate multiple texts to the same target language
        
        Args:
            target_language (str): Target language code
            texts (list): List of texts to translate
            
        Returns:
            list: List of translated texts
        """
        if not self.translate_client:
            print("Warning: Translation client not available for batch translation")
            return texts
            
        translated_texts = []
        
        for text in texts:
            translated_text = self.translate_text(target_language, text)
            translated_texts.append(translated_text)
            
        return translated_texts


# Test function for development
if __name__ == "__main__":
    # Test the translation API
    translate_api = TranslateApi()
    
    if translate_api.translate_client:
        print("Translation API test:")
        print(f"Supported languages: {len(translate_api.all_language_codes)}")
        
        # Test translation
        test_text = "Hello, how are you today?"
        translated = translate_api.translate_text('es', test_text)
        print(f"English: {test_text}")
        print(f"Spanish: {translated}")
        
        # Test language support
        print(f"Spanish supported: {translate_api.is_language_supported('es')}")
        print(f"Language name for 'es': {translate_api.get_language_name('es')}")
    else:
        print("Translation API not available - check credentials")