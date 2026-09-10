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

- **Pinokio** for the one-click launcher, with Python 3.10+ and Node.js 22+ in its toolchain.
- FFmpeg is supplied by `imageio-ffmpeg` on supported Windows, macOS, and Linux wheel platforms. A separate system installation is normally unnecessary. On other platforms, install FFmpeg and set `IMAGEIO_FFMPEG_EXE` to its executable path.
- The app enables Node.js and Deno for YouTube challenges. Standalone users need Node.js 22+ or Deno 2.3+ on `PATH`. The matching challenge scripts are installed through `yt-dlp[default]`; see the [yt-dlp setup guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

## Installation

1. Clone or download this repository
2. Open Pinokio
3. The app will show an "Install" button - click it to install dependencies
4. Once installed, click "Start" to launch the web UI

## Usage

1. Start the app from Pinokio (click "Start")
2. Click "Open Web UI" when prompted
3. Paste a YouTube link (e.g., `https://www.youtube.com/watch?v=...`)
4. Click "Download MP3"
5. Wait for the download to complete
6. Download the resulting MP3 file (or ZIP if multiple files)

## Project Structure

```
Youtube2MP3-Pinokio/
├── app/
│   ├── app.py          # Main Gradio application
│   └── requirements.txt
├── pinokio.js          # Pinokio app configuration
├── install.js          # Installation script
├── start.js            # Start script (launches the app)
├── update.js           # Update script
├── reset.js            # Reset script (removes the venv)
├── link.js             # Deduplication script
└── icon.jpg            # App icon
```

## Technical Details

- **Python Dependencies:**
  - `gradio` - Web UI framework
  - `yt-dlp` - YouTube downloader
  - `imageio-ffmpeg` - Bundled audio conversion executable

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
- **Update** - Fast-forwards the repository and upgrades dependencies within the supported version ranges. If local commits have diverged, Git stops so you can resolve them without an automatic merge.
- **Reset** - Removes `app/env` so dependencies can be reinstalled; keeps application code and downloads
- **Save Disk Space** - Deduplicates redundant library files

## Notes

- Each request stores its MP3s and ZIP in a separate folder under `app/downloads/`. Completed results remain available after later requests. Failed requests remove their own partial files.
- Completed downloads are retained until you delete them. After saving files you need and stopping the app, you can remove old folders under `app/downloads/` to reclaim space. Gradio also uses its own temporary file cache.
- The app accepts HTTP/HTTPS URLs on `youtube.com`, `www.youtube.com`, `m.youtube.com`, and `youtu.be`. Credentials and nonstandard ports are rejected.
- Multiple files are automatically zipped for download
- Progress is shown during the download process
- The server binds to `127.0.0.1`, with Gradio choosing an available port. Public sharing is disabled.

## Programmatic access

Start the app and use the address shown in Pinokio (the examples assume `http://127.0.0.1:7860`). The `/download` API takes one YouTube URL and returns a file plus a status message. The file is MP3 for one track or ZIP for multiple tracks. Invalid input and download failures return a null file with an explanatory status.

Python, using `gradio_client` (installed with the app):

```python
from gradio_client import Client

client = Client("http://127.0.0.1:7860")
file_path, status = client.predict(
    "https://www.youtube.com/watch?v=VIDEO_ID", api_name="/download"
)
print(file_path, status)
```

JavaScript, after installing `@gradio/client`:

```javascript
import { Client } from "@gradio/client";

const client = await Client.connect("http://127.0.0.1:7860");
const result = await client.predict("/download", [
  "https://www.youtube.com/watch?v=VIDEO_ID"
]);
console.log(result.data); // [file metadata (or null), status]
```

Curl uses Gradio's two-step event API. Submit the request:

```sh
curl -X POST http://127.0.0.1:7860/gradio_api/call/download \
  -H "Content-Type: application/json" \
  -d '{"data":["https://www.youtube.com/watch?v=VIDEO_ID"]}'
```

Copy the returned `event_id` into this request:

```sh
curl -N http://127.0.0.1:7860/gradio_api/call/download/EVENT_ID
```

The `complete` event contains `[file metadata, status]`; use the file metadata's `url` to retrieve the result. In PowerShell use `curl.exe` if `curl` is an alias.

## Development and checks

For standalone use, create a Python virtual environment in `app/env`, install `app/requirements.txt`, and run `python app.py` from `app/` with that environment activated. The supported Gradio API is version 6; Update keeps it within that major version.

Run the launcher tests from the repository root:

```sh
node --test tests/launchers.test.js
```

With the app environment activated, run the Python tests from `app/`:

```sh
python -m unittest discover -s tests -v
```

The tests cover request isolation, failure cleanup, input validation, ZIP packaging, launcher states, real FFmpeg conversion, and Gradio API file delivery. They use synthetic audio and mocked YouTube downloads, so they do not verify YouTube network access or account restrictions.

## License

Check the repository for license information.
