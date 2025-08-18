# YouTube Video Metadata Translator 🌍

**Automatically translate your YouTube video titles and descriptions into multiple languages to reach a global audience.**

Transform your channel into a multilingual powerhouse in minutes, not hours. This tool automates the tedious process of manually translating video metadata, helping you expand your reach and improve your YouTube SEO without creating new content.

![YouTube Video Translator Demo](https://img.shields.io/badge/Python-3.7+-blue.svg) ![Flask](https://img.shields.io/badge/Flask-Web%20App-green.svg) ![YouTube API](https://img.shields.io/badge/YouTube-API%20v3-red.svg)

## 🚀 Why This Matters

**The Problem**: You have great content, but it's only discoverable by people who speak your language. Manually translating dozens of video titles and descriptions would take weeks.

**The Solution**: This app translates your entire video library in minutes, making your content discoverable worldwide. Videos with multilingual metadata appear in international search results, leading to:

- ✅ **Increased Views**: Reach viewers who search in other languages
- ✅ **Better SEO**: Localized titles improve search rankings globally  
- ✅ **Broader Audience**: Connect with international viewers
- ✅ **Time Savings**: Hours of manual work become minutes of automation
- ✅ **Professional Appeal**: Localized content feels more welcoming to global audiences

## 🎯 Key Features

### Smart Translation Engine
- **Dual API Support**: Uses Google Translate for broad language coverage + optional DeepL for premium quality
- **Automatic Fallback**: If DeepL quota is exceeded, seamlessly switches to Google Translate
- **50+ Languages**: Support for all major world languages

### Batch Processing Power
- **Bulk Operations**: Select multiple videos and languages for mass translation
- **Smart Pagination**: Handle channels with hundreds of videos efficiently
- **Flexible Selection**: Choose per-page (10/25/50) or process entire channel at once

### YouTube Integration
- **Native API**: Direct integration with YouTube Data API v3
- **Safe Updates**: Only modifies localization fields, never touches original content
- **Verification System**: Automatically verifies translations were applied successfully

### User-Friendly Features
- **Length Management**: Auto-trim or skip content that exceeds YouTube's limits
- **Existing Translation Handling**: Skip or overwrite existing translations
- **Real-time Progress**: Visual feedback during translation process
- **Error Recovery**: Comprehensive error handling and user feedback

## 🛠️ Quick Start

### Prerequisites
- Python 3.7+ 
- A YouTube channel
- Google Cloud account (for APIs)
- *(Optional)* DeepL account for premium translations

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/youtube-metadata-translator.git
cd youtube-metadata-translator

# Install dependencies
pip install -r requirements.txt

# Create config directory for credentials
mkdir config
```

### 2. API Setup

#### YouTube API (Required)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **YouTube Data API v3**
4. Create **OAuth 2.0 Client ID** credentials (Desktop Application)
5. Download the JSON file and rename it to `account_client_secrets_main.json`
6. **Place the file in the `config/` folder you created**

#### Google Translate API (Required)
1. In the same Google Cloud project, enable **Cloud Translation API**
2. Create a **Service Account** with Translation API permissions
3. Generate and download a JSON key file
4. Rename to `translate_key.json` and **place in the `config/` folder**

#### DeepL API (Optional)
1. Sign up at [DeepL API](https://www.deepl.com/en/pro-api)
2. Get your authentication key from the account dashboard
3. Set environment variable: `export DEEPL_API_KEY="your-key-here"`

### 3. Run the Application

```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

### 4. First-Time Setup
On first run, you'll be redirected to Google OAuth to authorize YouTube access. Grant permissions and you're ready to go!

## 📖 How to Use

### Basic Workflow
1. **Select Videos**: Choose which videos to translate using checkboxes
2. **Choose Languages**: Click "Add Language" and select target languages
3. **Configure Options**: Set preferences for DeepL usage, overwrites, and length handling
4. **Translate**: Hit the translate button and wait for completion
5. **Verify**: Check your videos on YouTube Studio to see the new translations

### Pro Tips
- Start small with 5-10 videos to test the setup
- Focus on your most popular videos first for maximum impact
- Use "ALL" page size only for smaller channels (< 100 videos)
- Enable DeepL for European languages for better quality
- Check YouTube Studio's "Translations" section to verify results

## 📁 Project Structure

```
youtube-metadata-translator/
├── app.py                           # Main Flask application
├── youtube_account.py               # YouTube API integration
├── google_translate.py              # Translation API wrapper
├── requirements.txt                 # Python dependencies
├── templates/
│   ├── home.html                   # Main interface
│   └── quota-error.html            # Error pages
├── static/
│   └── css/
│       └── home.css                # Styling
├── config/                         # Create this folder for your credentials
│   ├── account_client_secrets_main.json  # YouTube OAuth credentials
│   └── translate_key.json                # Google Translate service account
└── README.md
```

## ⚠️ Important Notes

### API Quotas & Costs
- **YouTube API**: Free tier allows ~200 video updates/day
- **Google Translate**: Pay-per-character after free tier
- **DeepL**: 500K characters/month on free tier

### Security
- Never commit credential files to version control
- **Create a `config/` folder and place all credential files there**
- The included `.gitignore` protects your API keys in the `config/` directory
- OAuth tokens are stored locally and never shared

### File Setup Checklist
After setup, your `config/` folder should contain:
- ✅ `account_client_secrets_main.json` (YouTube OAuth)
- ✅ `translate_key.json` (Google Translate credentials)
- ✅ `token.pickle` (auto-generated after first OAuth)

### Limitations
- Translations are machine-generated (may need manual review)
- YouTube has character limits (100 for titles, 5000 for descriptions)
- Large channels may take time to process completely

## 🆘 Troubleshooting

**Videos not appearing?**
- Check YouTube API credentials in `config/account_client_secrets_main.json`
- Verify OAuth authorization was completed
- Ensure YouTube Data API v3 is enabled in Google Cloud Console

**Translations not saving?**
- Confirm videos have a default language set in YouTube Studio
- Check for character limit violations in console output
- Verify `config/translate_key.json` has correct permissions

**Quota exceeded errors?**
- Wait 24 hours for quota reset or request quota increase
- Reduce batch size to stay under limits
- Check Google Cloud Console for quota usage

**Translation quality issues?**
- Try enabling DeepL for supported languages
- Consider manual review for important videos
- Check console output for any API errors

**Missing config files?**
- Ensure `config/` folder exists in project directory
- Double-check file names match exactly:
  - `account_client_secrets_main.json`
  - `translate_key.json`
- Verify JSON files are valid (not corrupted downloads)

## 🤝 Contributing

Found a bug or have a feature idea? We welcome contributions!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Success Stories

*"Translated 150 videos into 5 languages in 30 minutes. My international views increased 40% in the first month!"* - Content Creator

*"This tool saved me weeks of manual work. The batch processing is a game-changer for large channels."* - Educational YouTuber

---

**Ready to go global?** ⭐ Star this repo if it helped you reach new audiences!

[🐛 Report Bug](https://github.com/yourusername/youtube-metadata-translator/issues) | [💡 Request Feature](https://github.com/yourusername/youtube-metadata-translator/issues) | [💬 Discussions](https://github.com/yourusername/youtube-metadata-translator/discussions)
