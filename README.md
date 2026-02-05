# Youtube2MP3

🎵 YouTube to MP3 downloader with a simple Gradio UI. Paste a YouTube link to download MP3 audio files.

## Description

Youtube2MP3 is a Pinokio app that provides a web-based interface for downloading YouTube videos as MP3 audio files. It uses `yt-dlp` for downloading and `ffmpeg` for audio conversion, wrapped in a clean Gradio interface.

## Features

- Simple web-based UI powered by Gradio
- Download YouTube videos as MP3 files
- Automatic audio extraction and conversion
- Progress tracking during downloads
- Support for single file downloads (returns MP3) or multiple files (returns ZIP)
- 192 kbps MP3 quality output

## Requirements

- **Pinokio** - This is a Pinokio app and requires Pinokio to run
- **ffmpeg** - Must be installed on your system for audio conversion
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `winget install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg` (Debian/Ubuntu) or `sudo yum install ffmpeg` (RHEL/CentOS)

## Installation

1. Clone or download this repository
2. Open Pinokio
3. The app will show an "Install" button - click it to install dependencies
4. Once installed, click "Start" to launch the web UI

## Usage

1. Start the app from Pinokio (click "Start")
2. Click "Open Web UI" when prompted
3. Paste a YouTube link (e.g., `https://www.youtube.com/watch?v=...`)
4. Click "Download"
5. Wait for the download to complete
6. Download the resulting MP3 file (or ZIP if multiple files)

## Project Structure

```
Youtube2DL-Pinokio/
├── app.py              # Main Gradio application
├── pinokio.js          # Pinokio app configuration
├── install.js          # Installation script
├── start.js            # Start script (launches the app)
├── update.js           # Update script
├── reset.js            # Reset script (removes app files)
├── link.js             # Deduplication script
├── requirements.txt    # Python dependencies
└── icon.png           # App icon
```

## Technical Details

- **Python Dependencies:**
  - `gradio` - Web UI framework
  - `yt-dlp` - YouTube downloader

- **Audio Settings:**
  - Format: MP3
  - Quality: 192 kbps
  - Codec: bestaudio/best

- **Supported URLs:**
  - `youtube.com`
  - `youtu.be`

## Pinokio Actions

- **Install** - Installs Python dependencies using `uv pip install`
- **Start** - Launches the Gradio web server
- **Update** - Updates the repository and dependencies
- **Reset** - Removes all installed files and resets to pre-install state
- **Save Disk Space** - Deduplicates redundant library files

## Notes

- Downloads are stored in temporary directories
- The app validates YouTube links before downloading
- Multiple files are automatically zipped for download
- Progress is shown during the download process

## License

Check the repository for license information.
