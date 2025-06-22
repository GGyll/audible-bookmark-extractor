# Audible Bookmark Extractor

## Overview

This tool allows you to download your Audible audiobooks and transcribe their bookmarks into text, which can then be exported. It features a modern graphical user interface for easy interaction.

Currently, the tool supports exporting to Excel and [Readwise](https://readwise.io/). We are working on adding support for Notion soon. If you use Readwise, you can connect it to Notion, Obsidian, or any other tool you use to manage your text files.

## Features

- Modern graphical user interface
- Audible authentication with 2FA support
- Book list management
- Bookmark extraction and transcription
- Export to Excel and Readwise
- Docker support for easy deployment

## Installation

### Option 1: Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/audible-bookmark-extractor.git
   cd audible-bookmark-extractor
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install FFMPEG:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
   - **Windows**: Download from [FFMPEG website](https://ffmpeg.org/download.html)

### Option 2: Docker Installation

1. Build the Docker image:
   ```bash
   docker build -t audible-extractor .
   ```

2. Run the container:
   ```bash
   docker run -d --name audible-extractor -p 8080:8080 audible-extractor
   ```

## Usage

### Running the Application

1. Start the application:
   - **Local installation**: 
     ```bash
     python gui.py
     ```
   - **Docker**:
     The application will start automatically when you run the container.

2. The application has three main tabs:
   - **Authentication**: Connect your Audible and Readwise accounts
   - **Books**: View and download your Audible books
   - **Export**: Export your bookmarks to Excel or Readwise

### Authentication

#### Audible Authentication
1. Go to the Authentication tab
2. Click "Authenticate with Audible"
3. Follow the prompts to enter your credentials
4. Complete the CAPTCHA verification if required

#### Readwise Authentication
1. Get your Readwise access token from [Readwise Access Token](https://readwise.io/access_token)
2. Enter the token in the Readwise authentication section
3. Click "Authenticate with Readwise"

### Managing Books

1. Go to the Books tab
2. Click "Refresh Book List" to see your Audible library
3. Select a book from the dropdown menu
4. Click "Download Selected Book" to download and process the book

### Exporting Bookmarks

1. Go to the Export tab
2. Choose your export method:
   - **Excel**: Select a location to save the file
   - **Readwise**: Directly export to your Readwise account

## Troubleshooting

### Common Issues

1. **FFMPEG Error**: 
   - Ensure FFMPEG is installed correctly on your system
   - For Docker, the image includes FFMPEG by default

2. **Authentication Issues**:
   - Ensure 2FA is enabled on your Amazon account
   - Check your internet connection
   - Try clearing the credentials and authenticating again

3. **GUI Not Starting**:
   - Ensure PyQt6 is installed correctly
   - Check system requirements for GUI applications

## Anti-Piracy Notice

This project does not crack Audible DRM or assist in downloading audiobooks you do not own. It allows users to use their own encryption key (retrieved from Audible's servers) to decrypt audiobooks, mirroring the process used by Audible's official software. This only applies to audiobooks legally purchased by the user.

This tool is intended solely for personal use, such as archiving, converting, or managing your legally purchased content. Decrypted audiobooks must not be distributed through public servers, torrents, or any other mass distribution channels.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.