"""Offline tests of the engine update of the Setup version (_update_engine_zip).

    python tests\test_engine.py

A fake "GitHub" runs on this PC (127.0.0.1) and serves SHA2-256SUMS and a yt-dlp zip.
Nothing is downloaded from the internet. Development only - not part of the release zip.
"""
import hashlib
import io
import os
import sys
import tempfile
import threading
import unittest
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import VideoDownloader as vd  # noqa: E402


def make_zip(with_version=True):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("yt_dlp/__init__.py", "")
        if with_version:
            z.writestr("yt_dlp/version.py", "__version__ = '2099.01.01'\n")
    return buf.getvalue()


class Fake(BaseHTTPRequestHandler):
    zip_bytes = b""
    sums = ""

    def log_message(self, *a): pass

    def do_GET(self):
        body = Fake.sums.encode() if self.path.endswith("SHA2-256SUMS") else Fake.zip_bytes
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers()
        self.wfile.write(body)


class EngineUpdate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        cls.tmp = tempfile.mkdtemp(prefix="vd_engine_test_")
        cls.saved = (vd.ENGINE_DIR, vd.ENGINE_ZIP, vd.ENGINE_URL, vd.ENGINE_SUMS_URL, vd.ENGINE_MAX_BYTES)
        vd.ENGINE_DIR = cls.tmp
        vd.ENGINE_ZIP = os.path.join(cls.tmp, "yt-dlp.zip")
        vd.ENGINE_URL = cls.base + "/yt-dlp"
        vd.ENGINE_SUMS_URL = cls.base + "/SHA2-256SUMS"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        vd.ENGINE_DIR, vd.ENGINE_ZIP, vd.ENGINE_URL, vd.ENGINE_SUMS_URL, vd.ENGINE_MAX_BYTES = cls.saved

    def setUp(self):
        for f in os.listdir(self.tmp):
            os.remove(os.path.join(self.tmp, f))
        vd.ENGINE_MAX_BYTES = 25 * 1024 * 1024

    def serve(self, data, sum_hex=None, name="yt-dlp"):
        Fake.zip_bytes = data
        Fake.sums = f"{sum_hex or hashlib.sha256(data).hexdigest()}  {name}\nffff  other-file\n"

    def test_good_release_is_installed_and_readable(self):
        self.serve(make_zip())
        self.assertTrue(vd._update_engine_zip())
        self.assertEqual(vd._zip_engine_version(), "2099.01.01")
        self.assertEqual(os.listdir(self.tmp), ["yt-dlp.zip"])            # no temp file left

    def test_wrong_checksum_is_refused_and_the_old_engine_stays(self):
        open(vd.ENGINE_ZIP, "wb").write(b"old")
        self.serve(make_zip(), sum_hex="0" * 64)
        self.assertFalse(vd._update_engine_zip())
        self.assertEqual(open(vd.ENGINE_ZIP, "rb").read(), b"old")
        self.assertEqual(os.listdir(self.tmp), ["yt-dlp.zip"])

    def test_missing_checksum_line_is_refused(self):
        self.serve(make_zip(), name="something-else")
        self.assertFalse(vd._update_engine_zip())
        self.assertEqual(os.listdir(self.tmp), [])

    def test_too_large_download_is_refused(self):
        vd.ENGINE_MAX_BYTES = 100
        self.serve(make_zip())
        self.assertFalse(vd._update_engine_zip())
        self.assertEqual(os.listdir(self.tmp), [])

    def test_a_zip_without_version_py_is_refused(self):
        self.serve(make_zip(with_version=False))
        self.assertFalse(vd._update_engine_zip())
        self.assertEqual(os.listdir(self.tmp), [])

    def test_a_non_zip_is_refused(self):
        self.serve(b"this is not a zip file")
        self.assertFalse(vd._update_engine_zip())

    def test_unreadable_zip_has_no_version(self):
        open(vd.ENGINE_ZIP, "wb").write(b"junk")
        self.assertEqual(vd._zip_engine_version(), "")


if __name__ == "__main__":
    unittest.main(verbosity=1)
