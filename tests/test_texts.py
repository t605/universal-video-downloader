"""Offline tests of text handling and temporary files (version 9.21).

    python tests\\test_texts.py

No window is opened. Development only - not part of the release zip.
"""
import os
import re
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import VideoDownloader as vd  # noqa: E402


def say(lang, key, **kw):
    return vd.App.t(SimpleNamespace(_lang=lang), key, **kw)


class TextHandling(unittest.TestCase):
    def test_english_singular(self):
        self.assertIn("Found 1 video.", say("en", "scan_found", n=1, folder="Downloads"))
        self.assertNotIn("1 videos", say("en", "scan_found", n=1, folder="Downloads"))
        self.assertIn("Found 2 videos.", say("en", "scan_found", n=2, folder="Downloads"))
        self.assertIn("Found 13 videos.", say("en", "scan_found", n=13, folder="Downloads"))

    def test_russian_button_names_do_not_break_across_lines(self):
        s = say("ru", "login_ok", host="x.example")
        self.assertIn("«Несколько видео на странице»", s)
        self.assertNotIn("«Несколько видео", s)

    def test_new_keys_exist_in_both_languages_with_the_same_placeholders(self):
        for key in ("scan_found", "scan_reading", "room_low_disk", "login_ok", "login_ok_unchecked"):
            for lang in ("en", "ru"):
                self.assertIn(key, vd.T[lang], f"{key} missing in {lang}")
            self.assertEqual(sorted(re.findall(r"{(\w+)}", vd.T["en"][key])),
                             sorted(re.findall(r"{(\w+)}", vd.T["ru"][key])), key)

    def test_status_messages_never_name_a_missing_placeholder(self):
        say("en", "scan_reading", i=3, n=13); say("ru", "scan_reading", i=3, n=13)
        say("en", "room_low_disk", gb="2.0", h=1); say("ru", "room_low_disk", gb="2.0", h=1)

    def test_russian_header_status_is_short(self):
        self.assertLessEqual(len(vd.T["ru"]["ready"]), 8)       # it was clipped at the minimum window size


class TemporaryCookieFiles(unittest.TestCase):
    def test_copies_are_removed_at_exit(self):
        fd, path = tempfile.mkstemp(prefix="vdl_vk_", suffix=".txt"); os.close(fd)
        vd._TEMP_COOKIES.append(path)
        vd._cleanup_temp_cookies()
        self.assertFalse(os.path.exists(path))
        vd._TEMP_COOKIES.clear()

    def test_old_leftovers_are_purged_new_ones_stay(self):
        fd, old = tempfile.mkstemp(prefix="vdl_vk_", suffix=".txt"); os.close(fd)
        os.utime(old, (time.time() - 7200, time.time() - 7200))
        fd, new = tempfile.mkstemp(prefix="vdl_vk_", suffix=".txt"); os.close(fd)
        try:
            vd._purge_old_temp_cookies(max_age=3600)
            self.assertFalse(os.path.exists(old))
            self.assertTrue(os.path.exists(new))
        finally:
            for f in (old, new):
                try: os.remove(f)
                except OSError: pass


if __name__ == "__main__":
    unittest.main(verbosity=1)
