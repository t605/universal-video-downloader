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


class FormatChain(unittest.TestCase):
    """The 480p chain must never end in "Requested format is not available" (a Kinescope stream with only
    484p and a separate sound stream did exactly that, 17 Nov 2026)."""

    def pick(self, formats):
        ydl = vd.yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True})
        sel = ydl.build_format_selector(vd.FORMAT_MERGE)
        chosen = list(sel({"formats": formats, "incomplete_formats": False}))
        self.assertTrue(chosen, "no format selected")
        c = chosen[0]
        return [f["format_id"] for f in (c.get("requested_formats") or [c])]

    @staticmethod
    def video(fid, h):
        return dict(format_id=fid, ext="mp4", url="u" + fid, height=h, width=h * 16 // 9, vcodec="avc1.64001f",
                    acodec="none", tbr=h * 1.4, protocol="m3u8_native")

    @staticmethod
    def audio(fid="a"):
        return dict(format_id=fid, ext="m4a", url="u" + fid, height=None, vcodec="none", acodec="mp4a.40.2",
                    tbr=64, protocol="m3u8_native")

    def test_only_484p_with_separate_sound(self):
        self.assertEqual(self.pick([self.audio(), self.video("v484", 484)]), ["v484", "a"])

    def test_480p_is_still_preferred_over_larger(self):
        self.assertEqual(self.pick([self.audio(), self.video("v480", 480), self.video("v720", 720),
                                    self.video("v1080", 1080)]), ["v480", "a"])

    def test_nothing_at_or_below_480p_takes_the_smallest_larger(self):
        self.assertEqual(self.pick([self.audio(), self.video("v720", 720), self.video("v1080", 1080)]), ["v720", "a"])

    def test_picture_with_sound_in_one_stream(self):
        muxed = dict(self.video("m360", 360), acodec="mp4a.40.2")
        self.assertEqual(self.pick([muxed]), ["m360"])


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
