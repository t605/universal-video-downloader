"""Offline tests of the school webinar pages (GetCourse /pl/webinar/show): recognising the link, reading the
stream address from the page, waiting until the broadcast is on air. No real website is contacted.

    python tests\\test_webinar.py

The page below is made up in the shape of a real one (made-up hash, no tokens).
Development only - not part of the release zip.
"""
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import VideoDownloader as vd  # noqa: E402

HASH = "ab" * 16
# The player settings as a real page holds them: JSON-escaped, plus a template with {hash}
PAGE = ("<script>var cfg = {playlist: 'https:\\/\\/stream13.getcourse.ru\\/playlist\\/" + HASH +
        "\\/master.m3u8?cdn=cloudflare\\u0026type=live', isRecordLesson: !!0};"
        "const liveMasterPlaylistTemplate = 'https://stream13.getcourse.ru/playlist/{hash}/master.m3u8?cdn=x&type=live';</script>")


class Site(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path.startswith("/pl/webinar/show?id=1"):
            body, code = PAGE.encode(), 200
        elif self.path.startswith("/pl/webinar/show?id=2"):
            body, code = b"<html>no player here</html>", 200
        else:
            body, code = b"gone", 404
        self.send_response(code); self.send_header("Content-Length", str(len(body))); self.end_headers()
        self.wfile.write(body)


class Link(unittest.TestCase):
    def test_school_webinar_pages_are_recognised(self):
        for ok in ("https://school.example/pl/webinar/show?id=3348296&view=1", "http://x.example/pl/webinar/view?id=1"):
            self.assertTrue(vd.is_gc_webinar_link(ok), ok)

    def test_other_links_are_not(self):
        for bad in ("https://school.example/room/abc", "https://www.example.com/watch?v=1", "", "hello",
                    "ftp://x.example/pl/webinar/show?id=1"):
            self.assertFalse(vd.is_gc_webinar_link(bad), bad)

    def test_rooms_are_still_accepted_by_the_room_rules(self):
        room, _ = vd.room_split_link("https://online.example/room/123?a=b")
        self.assertTrue(room.endswith("/room/123/"))


class StreamInPage(unittest.TestCase):
    def test_real_address_is_found_and_unescaped(self):
        u = vd.gc_stream_in_page(PAGE)
        self.assertEqual(u, f"https://stream13.getcourse.ru/playlist/{HASH}/master.m3u8?cdn=cloudflare&type=live")

    def test_template_alone_is_not_an_address(self):
        self.assertEqual(vd.gc_stream_in_page("var t = 'https://stream13.getcourse.ru/playlist/{hash}/master.m3u8?x=1';"), "")

    def test_find_players_lists_it_for_the_main_screen_and_the_scan(self):
        got = vd.find_players(PAGE)
        self.assertEqual([k for _, k in got], ["gcstream"])


class Reading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Site)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_page_is_read_and_named_after_its_id(self):
        url, name = vd.gc_webinar_stream(self.base + "/pl/webinar/show?id=1&view=1")
        self.assertIn(HASH, url)
        self.assertEqual(name, "webinar 1")

    def test_page_without_a_stream_has_its_own_message(self):
        with self.assertRaises(vd.RoomError) as c:
            vd.gc_webinar_stream(self.base + "/pl/webinar/show?id=2")
        self.assertEqual(c.exception.args[0], "room_err_gc_nostream")

    def test_unreadable_page_has_its_own_message(self):
        with self.assertRaises(vd.RoomError) as c:
            vd.gc_webinar_stream(self.base + "/pl/webinar/show?id=9")
        self.assertEqual(c.exception.args[0], "room_err_gc_page")


class Waiting(unittest.TestCase):
    def test_waits_until_the_playlist_answers(self):
        answers = [OSError("HTTP 500"), OSError("HTTP 500"), b"#EXTM3U\n#EXT-X-VERSION:3\n"]
        def fetch(u):
            a = answers.pop(0)
            if isinstance(a, Exception): raise a
            return a
        self.assertTrue(vd.gc_wait_for_playlist("https://x.example/p", "https://x.example", threading.Event(), poll=0.01, fetch=fetch))
        self.assertEqual(answers, [])

    def test_a_page_that_is_not_a_playlist_is_not_on_air(self):
        stop = threading.Event()
        calls = []
        def fetch(u):
            calls.append(1)
            if len(calls) >= 3: stop.set()
            return b"<html>error page</html>"
        self.assertFalse(vd.gc_wait_for_playlist("https://x.example/p", "https://x.example", stop, poll=0.01, fetch=fetch))

    def test_stop_ends_the_wait(self):
        stop = threading.Event(); stop.set()
        self.assertFalse(vd.gc_wait_for_playlist("https://x.example/p", "https://x.example", stop, poll=0.01,
                                                 fetch=lambda u: self.fail("must not ask after stop")))

    def test_fetch_wants_http_200_and_sends_the_school_as_referer(self):
        seen = {}
        def fake_http(url, data=None, headers=None, timeout=30):
            seen.update(headers or {}); return 500, b""
        old, vd._http = vd._http, fake_http
        try:
            with self.assertRaises(OSError):
                vd.gc_fetch("https://stream13.getcourse.ru/playlist/x/master.m3u8", "https://school.example")
        finally:
            vd._http = old
        self.assertEqual(seen.get("Referer"), "https://school.example/")


class Texts(unittest.TestCase):
    def test_new_messages_exist_in_both_languages(self):
        for key in ("room_err_link", "room_err_gc_page", "room_err_gc_nostream"):
            for lang in ("en", "ru"):
                self.assertIn(key, vd.T[lang])
        self.assertIn("/pl/webinar/show", vd.T["en"]["room_err_link"])
        self.assertIn("/pl/webinar/show", vd.T["ru"]["room_err_link"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
