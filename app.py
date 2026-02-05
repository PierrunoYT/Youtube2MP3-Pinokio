import os
import shutil
import tempfile
import zipfile
from typing import List, Optional, Tuple

import gradio as gr
import yt_dlp

YOUTUBE_HOSTS = ("youtube.com", "youtu.be")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _zip_if_needed(output_dir: str, downloaded_files: List[str]) -> Tuple[str, str]:
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
        if name.lower().endswith(".mp3"):
            files.append(os.path.join(output_dir, name))
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
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
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
    if not link or not link.strip():
        return None, "Please provide a YouTube link."

    link = link.strip()
    output_dir = tempfile.mkdtemp(prefix="downloads_")
    progress(0.01, desc="Validating link")

    try:
        if shutil.which("ffmpeg") is None:
            return None, "ffmpeg not found. Install ffmpeg and restart the app."

        if any(host in link for host in YOUTUBE_HOSTS):
            files = _yt_dlp_download([link], output_dir, progress)
            if not files:
                return None, "No files were downloaded. Check the link or ffmpeg."
            out_path, msg = _zip_if_needed(output_dir, files)
            return out_path, msg

        return None, "Unsupported link. Please use a YouTube link."
    except Exception as exc:
        return None, f"Error: {exc}"


def build_ui() -> gr.Blocks:
    theme = gr.themes.Soft(
        primary_hue="red",
        secondary_hue="slate",
        neutral_hue="slate",
    )
    with gr.Blocks(title="Youtube2MP3", theme=theme) as demo:
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
                - If you get errors, make sure `ffmpeg` is installed.
                - Large videos can take a few minutes to process.
                """
            )

        download_btn.click(
            fn=download_music,
            inputs=[link],
            outputs=[output_file, status],
        )
        clear_btn.click(
            fn=lambda: ("", None, ""),
            inputs=[],
            outputs=[link, output_file, status],
        )

    return demo


if __name__ == "__main__":
    build_ui().launch()
