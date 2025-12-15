# README.md

## Overview

This tool allows you to download your Audible audiobooks and transcribe their bookmarks into text, which can then be exported. 

Currently, the tool supports exporting to Excel and [Readwise](https://readwise.io/). We are working on adding support for Notion soon. If you use Readwise, you can connect it to Notion, Obsidian, or any other tool you use to manage your text files.

## Key Files

- **main.py**: The main entry point, primarily delegates to `command.py`.
- **command.py**: Processes command-line inputs.
- **audible_api.py**: Handles authentication and downloads audiobooks from Audible via the Audible API.
- **transcribe_api.py**: Uses Google Cloud Speech API to transcribe audiobooks into text.
- **readwise_api.py**: Manages exporting audiobook highlights to Readwise via the Readwise API.
- **notion_api.py**: (WIP) Will handle exporting audiobooks to Notion via the Notion API.

## Getting Started

1. Install the necessary packages:
   ```
   pip install -r requirements.txt
   ```

2. To run the program:
   ```
   python main.py
   ```

3. Type `help` in the command line for a list of available commands.

## Authentication

### Important: Two-Factor Authentication (2FA) is required for your Audible account.

### For Readwise:
1. Go to [Readwise Access Token](https://readwise.io/access_token) to get your access token.
2. Copy and paste the token into the command line when prompted.

### Audible Authentication:
Run the following command to authenticate:
```
authenticate
```

When prompted, enter your Audible email and password. A separate window will open for CAPTCHA verification; you will be prompted to solve the CAPTCHA. Audible CAPTCHAs can be challenging, so you may need to retry a few times to get a solvable one.

After successful authentication, your credentials are stored in `credentials.json`, so you won't need to authenticate again as long as this file is present.

### Readwise Authentication:
If you plan to post your audiobook highlights to Readwise, authenticate with Readwise using:
```
readwise_authenticate
```

Your credentials will be stored in `readwise_token.json`, and you won't need to authenticate again as long as this file is present.

### Posting Highlights to Readwise:
Once you've extracted and converted highlights, they are stored in:
```
~/audible-bookmark-extractor/<<bookname>>/transcribed_clips/contents.json
```

Run the following command to post your highlights:
```
readwise_post_highlights
```

Once posted, you can visit [Readwise Books](https://readwise.io/books) to see the highlights uploaded from this app.

## Processing Books

### Quick Start: Full Pipeline Command

The easiest way to process a book is using the `process_book` command, which runs all four steps automatically:

1. First, list your books to see their index numbers:
   ```
   list_books
   ```

2. Then run the full pipeline for a specific book:
   ```
   process_book --index=3
   ```
   (Replace `3` with the index number of your book)

This single command will:
- Download the audiobook
- Convert it to MP3 (removing DRM)
- Extract all bookmarks
- Transcribe the bookmarks

The command will show progress for each step and handle errors gracefully.

**Smart Resume:** The pipeline automatically detects and skips completed steps. If it crashes or you interrupt it, just run the same command again and it will resume where it left off.

**Manual Step Control:** You can also skip specific steps manually:
```
process_book --index=3 --skip-download=true              # Skip download only
process_book --index=3 --skip-download=true --skip-convert=true   # Start from bookmarks
```

Available skip flags: `--skip-download`, `--skip-convert`, `--skip-bookmarks`, `--skip-transcribe`

### Manual Step-by-Step Process

If you prefer to run each step individually, you can use these commands in order:

1. **Download books:**
   ```
   download_books
   ```

2. **Convert audiobook to MP3:**
   ```
   convert_audiobook
   ```

3. **Extract bookmarks:**
   ```
   get_bookmarks
   ```

4. **Transcribe bookmarks:**
   ```
   transcribe_bookmarks
   ```

Each command will prompt you to select a book from your library.

## Transcription

- OpenAI Whisper (optional): Provide an API key via `openai_authenticate` to use Whisper-based transcription.
- Google Speech Recognition (default fallback): If no OpenAI key is provided, the app uses the SpeechRecognition library’s Google recognizer; no API key required.

## FFMPEG Setup

In addition to `ffmpeg-python`, you need to install FFMPEG on your system. For installation details, refer to the [python-ffmpeg documentation](https://github.com/kkroening/ffmpeg-python).

## Anti-Piracy Notice

This project does not crack Audible DRM or assist in downloading audiobooks you do not own. It allows users to use their own encryption key (retrieved from Audible’s servers) to decrypt audiobooks, mirroring the process used by Audible's official software. This only applies to audiobooks legally purchased by the user.

This tool is intended solely for personal use, such as archiving, converting, or managing your legally purchased content. Decrypted audiobooks must not be distributed through public servers, torrents, or any other mass distribution channels. We will not provide support to those involved in such activities. Remember, authors, retailers, and publishers depend on fair compensation to continue producing the audiobooks we all enjoy. Please respect their rights.

This software is intended as a backup solution for your own audiobooks, should Audible services fail for any reason. Additionally, it provides a way to export your bookmarks to an Excel file for easier reference, instead of relying solely on the Audible app.

## FAQ

**Error:** `sh: 1: ffmpeg: not found`  
**Solution:** Install FFMPEG. For details, refer to the [python-ffmpeg documentation](https://github.com/kkroening/ffmpeg-python).

---

**Issue:** _I’m prompted for a CVF code during authentication, and the program crashes._  
**Solution:** Ensure that Two-Factor Authentication (2FA) is enabled on your Amazon account.

---

**Error:** `"Exception: Login failed. Please check the log."` during authentication.  
**Solution:** Ensure that Two-Factor Authentication (2FA) is enabled on your Amazon account.