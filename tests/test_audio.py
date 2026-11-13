"""Offline tests for the "Sound only (MP3)" option (no internet, no window).

    python tests\test_audio.py

Development only - not part of the release zip.
"""
import os
import re
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import VideoDownloader as vd  # noqa: E402


def fake_app(ffmpeg):
    return SimpleNamespace(_skip_ssl=lambda: False, _ssl_mode="auto",
                           _ffmpeg=ffmpeg, _dl_dir=os.getcwd())


class AudioOptions(unittest.TestCase):
    def test_video_is_unchanged(self):
        o = vd.App._base_opts(fake_app("ffmpeg.exe"))
        self.assertEqual(o["format"], vd.FORMAT_MERGE)
        self.assertEqual(o["merge_output_format"], "mp4")
        self.assertNotIn("postprocessors", o)

    def test_audio_makes_mp3(self):
        o = vd.App._base_opts(fake_app("ffmpeg.exe"), audio=True)
        self.assertEqual(o["format"], "bestaudio/best")
        self.assertNotIn("merge_output_format", o)
        pp = o["postprocessors"][0]
        self.assertEqual((pp["key"], pp["preferredcodec"]), ("FFmpegExtractAudio", "mp3"))
        self.assertEqual(o["ffmpeg_location"], "ffmpeg.exe")

    def test_audio_without_ffmpeg_stays_video_options(self):
        # _start_download refuses before this point; the options must never ask for MP3 alone
        o = vd.App._base_opts(fake_app(None), audio=True)
        self.assertNotIn("postprocessors", o)
        self.assertEqual(o["format"], vd.FORMAT_SINGLE)

    def test_info_only_has_no_format(self):
        o = vd.App._base_opts(fake_app("ffmpeg.exe"), info_only=True, audio=True)
        self.assertNotIn("format", o)


class AudioTexts(unittest.TestCase):
    KEYS = ("download_audio", "mode_video", "mode_audio", "st_done_audio",
            "st_finishing_audio", "st_done_n_audio", "d_ffmpeg_audio",
            "page_video_only", "st_link_ok")

    def test_keys_in_both_languages(self):
        for k in self.KEYS:
            self.assertIn(k, vd.T["en"], k)
            self.assertIn(k, vd.T["ru"], k)

    def test_placeholders_match(self):
        for k in self.KEYS:
            self.assertEqual(sorted(re.findall(r"{(\w+)}", vd.T["en"][k])),
                             sorted(re.findall(r"{(\w+)}", vd.T["ru"][k])), k)

    def test_link_ok_names_the_button(self):
        for lang in ("en", "ru"):
            self.assertIn("{btn}", vd.T[lang]["st_link_ok"])


class DrmMessage(unittest.TestCase):
    def test_drm_error_gets_its_own_plain_message(self):
        for err in ("ERROR: This format is DRM protected; Try selecting another format",
                    "This video is DRM-protected", "video has DRM"):
            self.assertEqual(vd.App._diagnose(None, err), ("d_drm", "err", None))
        for lang in ("en", "ru"):
            self.assertIn("d_drm", vd.T[lang])

    def test_other_errors_are_not_called_drm(self):
        self.assertNotEqual(vd.App._diagnose(None, "HTTP Error 403: Forbidden")[0], "d_drm")

if __name__ == "__main__":
    unittest.main()
