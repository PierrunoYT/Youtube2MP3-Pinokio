import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import zipfile

import app


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'downloads'
        self.root_patch = patch.object(app, 'OUTPUT_DIR', str(self.root))
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.progress = lambda *args, **kwargs: None

    def download(self, link='https://youtu.be/example'):
        return app.download_music(link, self.progress)

    @staticmethod
    def fake_download(targets, output_dir, progress):
        result = Path(output_dir) / 'track.mp3'
        result.write_bytes(b'audio')
        return [str(result)]

    def test_validation(self):
        for url in ['https://youtu.be/abc', 'http://www.youtube.com/watch?v=abc',
                    'https://m.youtube.com/playlist?list=abc', 'https://YOUTUBE.COM/shorts/abc']:
            self.assertTrue(app._is_youtube_link(url), url)
        for url in ['ftp://youtube.com/x', '//youtube.com/x', 'https://youtube.com.evil.test',
                    'https://evil.test/youtube.com', 'https://user@youtube.com/x',
                    'https://youtube.com:bad/x', 'https://youtube.com:1234/x',
                    'https://[youtube.com', 'https://you\ntube.com/x']:
            self.assertFalse(app._is_youtube_link(url), url)

    def test_invalid_input_does_not_touch_downloads(self):
        self.root.mkdir()
        previous = self.root / 'previous.mp3'
        previous.write_bytes(b'keep')
        with patch.object(app, '_yt_dlp_download') as downloader:
            for value in [None, 42, '', '  ', 'https://example.com']:
                self.assertIsNone(self.download(value)[0])
            downloader.assert_not_called()
        self.assertEqual(previous.read_bytes(), b'keep')

    def test_sequential_results_remain_available(self):
        with patch.object(app, '_yt_dlp_download', side_effect=self.fake_download):
            first, _ = self.download()
            second, _ = self.download()
        self.assertNotEqual(first, second)
        self.assertTrue(Path(first).is_file())
        self.assertTrue(Path(second).is_file())

    def test_concurrent_requests_have_separate_results(self):
        barrier = threading.Barrier(2)
        def download(*args):
            barrier.wait(timeout=10)
            return self.fake_download(*args)
        with patch.object(app, '_yt_dlp_download', side_effect=download):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: self.download(), range(2)))
        self.assertNotEqual(results[0][0], results[1][0])
        self.assertTrue(all(Path(result[0]).is_file() for result in results))

    def test_failure_cleans_only_its_request(self):
        with patch.object(app, '_yt_dlp_download', side_effect=self.fake_download):
            previous, _ = self.download()
        def fail(targets, output_dir, progress):
            (Path(output_dir) / 'partial.part').write_bytes(b'partial')
            raise RuntimeError('download failed')
        with patch.object(app, '_yt_dlp_download', side_effect=fail):
            result, status = self.download()
        self.assertIsNone(result)
        self.assertIn('download failed', status)
        self.assertTrue(Path(previous).is_file())
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_storage_error_becomes_status(self):
        with patch.object(app, '_ensure_dir', side_effect=PermissionError('read only')):
            result, status = self.download()
        self.assertIsNone(result)
        self.assertIn('read only', status)

    def test_empty_download_is_cleaned(self):
        with patch.object(app, '_yt_dlp_download', return_value=[]):
            result, status = self.download()
        self.assertIsNone(result)
        self.assertIn('No files', status)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_packaging_and_file_collection(self):
        self.root.mkdir()
        (self.root / 'directory.mp3').mkdir()
        (self.root / 'partial.part').write_bytes(b'partial')
        for name in ['one.mp3', 'two.MP3']:
            (self.root / name).write_bytes(b'audio')
        files = app._collect_output_files(str(self.root))
        self.assertEqual(len(files), 2)
        archive, status = app._zip_if_needed(str(self.root), files)
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(zipped.namelist(), ['one.mp3', 'two.MP3'])
            self.assertEqual(zipped.read('one.mp3'), b'audio')
        self.assertIn('2 files', status)
        with self.assertRaises(ValueError):
            app._zip_if_needed(str(self.root), [])

    def test_same_title_videos_get_distinct_paths(self):
        with patch.object(app.yt_dlp, 'YoutubeDL') as downloader:
            app._yt_dlp_download(['https://youtu.be/example'], str(self.root), self.progress)
            options = downloader.call_args.args[0]
        with app.yt_dlp.YoutubeDL(options) as ydl:
            first = ydl.prepare_filename({'title': 'Same title', 'id': 'first', 'ext': 'webm'})
            second = ydl.prepare_filename({'title': 'Same title', 'id': 'second', 'ext': 'webm'})
        self.assertNotEqual(first, second)
        self.assertEqual(os.path.dirname(first), str(self.root))

    def test_error_messages_have_no_terminal_colors(self):
        with patch.object(app.yt_dlp, 'YoutubeDL') as downloader:
            app._yt_dlp_download(['https://youtu.be/example'], str(self.root), self.progress)
            options = downloader.call_args.args[0]
        ydl_module = sys.modules['yt_dlp.YoutubeDL']
        env = {k: v for k, v in os.environ.items() if k != 'NO_COLOR'}
        env['TERM'] = 'xterm'
        with patch.object(ydl_module, 'supports_terminal_sequences', return_value=True), \
                patch.dict(os.environ, env, clear=True), app.yt_dlp.YoutubeDL(options) as ydl:
            with self.assertRaises(app.yt_dlp.utils.DownloadError) as error:
                ydl.report_error('boom')
        self.assertNotIn('\x1b', str(error.exception))


if __name__ == '__main__':
    unittest.main()
