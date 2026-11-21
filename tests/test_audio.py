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


class FreeNames(unittest.TestCase):
    """A download never overwrites a file and is never skipped: 'view', 'view (1)', 'view (2)' (owner's rule 2026-11-20:
    every GetCourse lesson page ends in /view, so all lessons got the same name)."""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def opts(self, name="view"):
        return {"outtmpl": os.path.join(self.dir, name + ".%(ext)s")}

    @staticmethod
    def writer(*files, fail=False):
        """a stand-in for yt-dlp: writes the given (name, text) files next to the outtmpl it is given"""
        def run(o):
            folder = os.path.dirname(o["outtmpl"])
            for name, text in files:
                with open(os.path.join(folder, name), "w") as f:
                    f.write(text)
            if fail:
                raise RuntimeError("download stopped")
            return "done"
        return run

    def names(self):
        return sorted(os.listdir(self.dir))

    def test_same_name_three_times(self):
        for i in (1, 2, 3):
            vd.run_into_free_names(self.opts(), self.writer(("view.mp4", f"video {i}")))
        self.assertEqual(self.names(), ["view (1).mp4", "view (2).mp4", "view.mp4"])
        content = {}
        for n in self.names():
            with open(os.path.join(self.dir, n)) as f:
                content[n] = f.read()
        self.assertEqual(content, {"view.mp4": "video 1", "view (1).mp4": "video 2", "view (2).mp4": "video 3"})

    def test_an_existing_file_is_left_untouched(self):
        with open(os.path.join(self.dir, "view.mp4"), "w") as f:
            f.write("old")
        vd.run_into_free_names(self.opts(), self.writer(("view.mp4", "new")))
        for name, want in (("view.mp4", "old"), ("view (1).mp4", "new")):
            with open(os.path.join(self.dir, name)) as f:
                self.assertEqual(f.read(), want)

    def test_returns_the_result_and_leaves_no_hidden_folder(self):
        self.assertEqual(vd.run_into_free_names(self.opts(), self.writer(("view.mp4", "x"))), "done")
        self.assertFalse([n for n in self.names() if n.startswith(".vdl_")])

    def test_unfinished_pieces_are_not_delivered(self):
        vd.run_into_free_names(self.opts(), self.writer(
            ("view.mp4", "ok"), ("view.mp4.part", "half"), ("view.f137.mp4", "video only"), ("view.f140.m4a", "audio only")))
        self.assertEqual(self.names(), ["view.mp4"])

    def test_a_failed_download_still_delivers_the_files_it_finished(self):
        with self.assertRaises(RuntimeError):
            vd.run_into_free_names(self.opts(), self.writer(("one.mp4", "1"), ("two.mp4.part", "half"), fail=True))
        self.assertEqual(self.names(), ["one.mp4"])

    def test_options_without_a_template_run_unchanged(self):
        seen = []
        vd.run_into_free_names({"format": "best"}, lambda o: seen.append(o) or "x")
        self.assertEqual(seen, [{"format": "best"}])

    def test_the_template_the_downloader_sees_is_inside_a_sub_folder(self):
        got = []
        vd.run_into_free_names(self.opts("lesson"), lambda o: got.append(o["outtmpl"]))
        self.assertNotEqual(os.path.dirname(got[0]), self.dir)
        self.assertTrue(got[0].endswith("lesson.%(ext)s"))


if __name__ == "__main__":
    unittest.main()
