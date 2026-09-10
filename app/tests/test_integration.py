"""Offline integration checks using real Gradio and FFmpeg dependencies."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

import gradio_client
import imageio_ffmpeg
import yt_dlp
from yt_dlp.postprocessor import FFmpegExtractAudioPP

import app


class IntegrationTests(unittest.TestCase):
    def test_bundled_ffmpeg_converts_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'test.wav'
            with wave.open(str(source), 'wb') as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(44100)
                audio.writeframes(b'\x00\x00' * 44100)
            with yt_dlp.YoutubeDL({'quiet': True, 'ffmpeg_location': imageio_ffmpeg.get_ffmpeg_exe()}) as ydl:
                processor = FFmpegExtractAudioPP(ydl, preferredcodec='mp3', preferredquality='192')
                _, result = processor.run({'filepath': str(source), 'ext': 'wav', 'vcodec': 'none'})
            self.assertEqual(result['ext'], 'mp3')
            self.assertGreater(Path(result['filepath']).stat().st_size, 0)

    def test_gradio_api_validation_and_file_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            demo = app.build_ui()
            self.addCleanup(demo.close)
            with patch.dict(os.environ, {'GRADIO_ANALYTICS_ENABLED': 'False'}):
                _, url, _ = demo.launch(theme=app._THEME, server_name='127.0.0.1',
                                        share=False, prevent_thread_lock=True, quiet=True)
            client = gradio_client.Client(url, verbose=False)
            invalid = client.predict('https://example.com', api_name='/download')
            self.assertIsNone(invalid[0])
            self.assertIn('Unsupported', invalid[1])
            def fake_download(targets, output_dir, progress):
                file_path = Path(output_dir) / 'track.mp3'
                file_path.write_bytes(b'test audio')
                return [str(file_path)]
            with patch.object(app, 'OUTPUT_DIR', directory), patch.object(
                    app, '_yt_dlp_download', side_effect=fake_download):
                result = client.predict('https://youtu.be/example', api_name='/download')
            self.assertEqual(Path(result[0]).read_bytes(), b'test audio')
            self.assertEqual(result[1], 'Downloaded 1 file.')
            demo.close()


if __name__ == '__main__':
    unittest.main()
