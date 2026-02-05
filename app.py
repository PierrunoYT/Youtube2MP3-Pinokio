import os
import tempfile
import zipfile
from typing import List, Tuple

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


def download_music(link: str, progress=gr.Progress()) -> Tuple[str, str]:
    if not link or not link.strip():
        return "", "Please provide a YouTube link."

    link = link.strip()
    output_dir = tempfile.mkdtemp(prefix="downloads_")
    progress(0.01, desc="Validating link")

    try:
        if any(host in link for host in YOUTUBE_HOSTS):
            files = _yt_dlp_download([link], output_dir, progress)
            if not files:
                return "", "No files were downloaded. Check the link or ffmpeg."
            out_path, msg = _zip_if_needed(output_dir, files)
            return out_path, msg

        return "", "Unsupported link. Please use a YouTube link."
    except Exception as exc:
        return "", f"Error: {exc}"


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Youtube2MP3") as demo:
        gr.Markdown("Paste a YouTube link to download MP3.")
        link = gr.Textbox(label="YouTube link", placeholder="https://...")
        download_btn = gr.Button("Download")
        output_file = gr.File(label="Download file")
        status = gr.Textbox(label="Status", interactive=False)

        download_btn.click(
            fn=download_music,
            inputs=[link],
            outputs=[output_file, status],
        )

    return demo


if __name__ == "__main__":
    build_ui().launch()
