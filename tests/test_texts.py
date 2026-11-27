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
        self.assertIn("«Несколько\u00a0видео»", s)
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


class PrivateLinksAreMasked(unittest.TestCase):
    """The activity log is sent to the helper ("Copy the log"): a link in it must not let anybody log in as the user,
    and must not hold a name, an e-mail or a phone number."""
    LINKS = ("Scan: https://school.example/g/123456/AbCdEf1234567890?v=ZZsecret&x=1",
             "Link taken from the clipboard: https://room.example/room/7/a?username=Anna+Testova&email=anna.testova%40example.org&phone=+70000000000",
             "ERROR: HTTP 404 for veb?username=Anna+Testova&email=anna.testova@example.org&pho",
             "went to: /g/123456/AbCdEf1234567890",
             "Opening https://anna:pw123secret@school.example/page#token=ZZsecret")
    SECRETS = ("AbCdEf1234567890", "ZZsecret", "Testova", "testova", "70000000000", "pw123secret")

    def check(self, text):
        for s in self.SECRETS:
            self.assertNotIn(s, text)

    def test_scrub_removes_everything_that_identifies_the_user(self):
        for line in self.LINKS:
            self.check(vd.scrub(line))
        self.assertIn("school.example", vd.scrub(self.LINKS[0]))        # the helper still sees which site it was

    def test_a_name_with_a_space_is_masked_whole(self):
        self.assertNotIn("Testova", vd.scrub("veb?username=Anna Testova&email=a@example.org"))

    def test_a_very_long_line_is_masked_quickly(self):
        start = time.time()
        vd.scrub("x" * 60000)
        self.assertLess(time.time() - start, 1.0)

    def test_ordinary_lines_stay_as_they_are(self):
        for line in ("Recording to: Lesson (1).ts", "   Playlist address: cdn.example/stream/live.m3u8", "Saving to: D:/Videos"):
            self.assertEqual(vd.scrub(line), line)

    def test_the_activity_log_and_its_copy_hold_masked_lines_only(self):
        app = SimpleNamespace(_log_lines=[], _log_insert=lambda text, tag: None)
        for line in self.LINKS:
            vd.App._log(app, line)
        self.check("\n".join(t for t, _ in app._log_lines))

    def test_the_log_file_under_pythonw_is_masked_too(self):
        import io
        buf = io.StringIO()
        out = vd.ScrubbedFile(buf)
        for line in self.LINKS:
            out.write(line + "\n")
        out.flush()
        self.check(buf.getvalue())
        self.assertFalse(hasattr(out, "buffer"))                        # a library must not write around the mask


class SafeDefaultAnswers(unittest.TestCase):
    """A stray press of Enter must never delete saved logins or start a recording on a nearly full disk."""

    def ask(self, call):
        asked = []
        old = vd.messagebox.askyesno
        vd.messagebox.askyesno = lambda *a, **k: asked.append(k) or False
        try:
            call()
        finally:
            vd.messagebox.askyesno = old
        self.assertEqual([k.get("default") for k in asked], ["no"])

    def test_log_out_preselects_no(self):
        old = vd.LOGIN_DIR
        vd.LOGIN_DIR = tempfile.mkdtemp()
        saved = os.path.join(vd.LOGIN_DIR, "school.example.txt")
        open(saved, "w").close()
        try:
            self.ask(lambda: vd.App._logout(SimpleNamespace(t=lambda key, **kw: key)))
            self.assertTrue(os.path.exists(saved))
        finally:
            vd.LOGIN_DIR = old

    def test_low_disk_question_preselects_no(self):
        old = vd.shutil.disk_usage
        vd.shutil.disk_usage = lambda p: SimpleNamespace(total=1, used=1, free=2 * 1024 ** 3)
        app = SimpleNamespace(_running=False, _room_var=SimpleNamespace(get=lambda: "https://r.example/room/1/a"),
                              _ffmpeg="ffmpeg", _dl_dir=".", _lang="en", t=lambda key, **kw: key,
                              _set_status=lambda *a, **k: None)
        try:
            self.ask(lambda: vd.App._start_room(app))
        finally:
            vd.shutil.disk_usage = old


class NameAndEmailDialog(unittest.TestCase):
    def app(self, page, main="", room=""):
        return SimpleNamespace(_page=page, _url_var=SimpleNamespace(get=lambda: main), _room_var=SimpleNamespace(get=lambda: room))

    def test_the_address_is_taken_from_the_page_the_user_came_from(self):
        lesson, webinar = "https://school.example/lesson/1", "https://school.example/pl/webinar/show?id=5"
        self.assertEqual(vd.App._entry_link(self.app("cookies", lesson, webinar)), lesson)
        self.assertEqual(vd.App._entry_link(self.app("main", lesson, webinar)), lesson)
        self.assertEqual(vd.App._entry_link(self.app("room", lesson, webinar)), webinar)
        self.assertEqual(vd.App._entry_link(self.app("cookies", "", webinar)), webinar)
        self.assertEqual(vd.App._entry_link(self.app("cookies", "http://x.example/a", "")), "")

    def test_a_typed_phone_goes_into_the_room_link(self):
        q = vd.room_split_link(vd.room_link_with("https://r.example/room/1/a", "N", "n@example.org", "+1000"))[1]
        self.assertEqual(q["phone"], "+1000")
        q = vd.room_split_link(vd.room_link_with("https://r.example/room/1/a?phone=5", "N", "n@example.org"))[1]
        self.assertEqual(q["phone"], "5")                       # nothing typed: the link keeps what it had

    def test_the_consent_names_everything_that_is_sent(self):
        self.assertIn("phone", vd.T["en"]["enter_consent"])
        self.assertIn("телефон", vd.T["ru"]["enter_consent"])


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
