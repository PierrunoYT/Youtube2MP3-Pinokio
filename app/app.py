import os
import shutil
import tempfile
import zipfile
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import gradio as gr
import imageio_ffmpeg
import yt_dlp

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")

YOUTUBE_HOSTS = ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be")


def _is_youtube_link(link: str) -> bool:
    try:
        parsed = urlparse(link)
        host = parsed.hostname or ""
        if (parsed.scheme not in ("http", "https") or parsed.username is not None
                or parsed.password is not None or parsed.port not in (None, 80, 443)
                or any(char.isspace() or ord(char) < 32 for char in link)):
            return False
    except (ValueError, TypeError, AttributeError):
        return False
    host = host.lower()
    return host in YOUTUBE_HOSTS


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _zip_if_needed(output_dir: str, downloaded_files: List[str]) -> Tuple[str, str]:
    if not downloaded_files:
        raise ValueError("No MP3 files to package.")
    if len(downloaded_files) == 1:
        return downloaded_files[0], "Downloaded 1 file."

    zip_path = os.path.join(output_dir, "downloads.zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for file_path in downloaded_files:
            zipf.write(file_path, arcname=os.path.basename(file_path))
    return zip_path, f"Downloaded {len(downloaded_files)} files (zipped)."


def _collect_output_files(output_dir: str) -> List[str]:
    files = []
    for name in os.listdir(output_dir):
        file_path = os.path.join(output_dir, name)
        if name.lower().endswith(".mp3") and os.path.isfile(file_path):
            files.append(file_path)
    return sorted(files)


def _yt_dlp_download(
    targets: List[str], output_dir: str, progress: gr.Progress
) -> List[str]:
    _ensure_dir(output_dir)
    status = {"current": "", "percent": 0}

    def _hook(d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            if total:
                status["percent"] = int(downloaded * 100 / total)
            status["current"] = d.get("filename", "")
            progress(
                min(status["percent"] / 100, 0.95),
                desc=f"Downloading {os.path.basename(status['current'])}",
            )

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title).100B [%(id)s].%(ext)s"),
        "quiet": True,
        "color": {"stdout": "no_color", "stderr": "no_color"},
        "js_runtimes": {"deno": {}, "node": {}},
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
        "progress_hooks": [_hook],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for idx, target in enumerate(targets, start=1):
            progress(0.05, desc=f"Preparing {idx}/{len(targets)}")
            ydl.download([target])

    progress(0.98, desc="Finalizing")
    return _collect_output_files(output_dir)


def download_music(link: str, progress=gr.Progress()) -> Tuple[Optional[str], str]:
    if not isinstance(link, str) or not link.strip():
        return None, "Please provide a YouTube link."

    link = link.strip()
    if not _is_youtube_link(link):
        return None, "Unsupported link. Please use an HTTP or HTTPS YouTube link."

    output_dir = None
    try:
        progress(0.01, desc="Validating link")
        _ensure_dir(OUTPUT_DIR)
        output_dir = tempfile.mkdtemp(prefix="download-", dir=OUTPUT_DIR)
        files = _yt_dlp_download([link], output_dir, progress)
        if not files:
            shutil.rmtree(output_dir, ignore_errors=True)
            return None, "No files were downloaded. Check the link or ffmpeg."
        out_path, msg = _zip_if_needed(output_dir, files)
        progress(1.0, desc="Complete")
        return out_path, msg
    except Exception as exc:
        if output_dir is not None:
            shutil.rmtree(output_dir, ignore_errors=True)
        return None, f"Error: {exc}"


_THEME = gr.themes.Soft(
    primary_hue="red",
    secondary_hue="slate",
    neutral_hue="slate",
)


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Youtube2MP3") as demo:
        gr.Markdown(
            """
            # Youtube2MP3
            Convert a YouTube video to MP3 in one click.
            """
        )

        with gr.Row():
            with gr.Column(scale=3):
                link = gr.Textbox(
                    label="YouTube link",
                    placeholder="https://www.youtube.com/watch?v=...",
                )
            with gr.Column(scale=1, min_width=160):
                download_btn = gr.Button("Download MP3", variant="primary")
                clear_btn = gr.Button("Clear", variant="secondary")

        with gr.Row():
            output_file = gr.File(
                label="Your download",
                file_count="single",
            )
            status = gr.Textbox(label="Status", interactive=False)

        with gr.Accordion("Tips", open=False):
            gr.Markdown(
                """
                - Use a full YouTube URL or short youtu.be link.
                - Audio conversion uses bundled FFmpeg. Use Update if downloads fail.
                - Large videos can take a few minutes to process.
                """
            )

        download_btn.click(
            fn=download_music,
            inputs=[link],
            outputs=[output_file, status],
            api_name="download",
        )
        clear_btn.click(
            fn=lambda: ("", None, ""),
            inputs=[],
            outputs=[link, output_file, status],
            api_name=False,
        )

    return demo


if __name__ == "__main__":
    build_ui().launch(
        theme=_THEME,
        server_name="127.0.0.1",
        share=False,
        allowed_paths=[OUTPUT_DIR],
    )
