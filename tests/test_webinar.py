"""Offline tests of the school webinar pages (GetCourse /pl/webinar/show): recognising the link, reading the
stream address from the page, waiting until the broadcast is on air. No real website is contacted.

    python tests\\test_webinar.py

The page below is made up in the shape of a real one (made-up hash, no tokens).
Development only - not part of the release zip.
"""
import json
import os
import struct
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
        for ok in ("https://school.example/pl/webinar/show?id=1000001&view=1", "http://x.example/pl/webinar/view?id=1"):
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


# ---------------------------------------------------------------- scheduled recordings ("auto-webinar")
AUTO_PAGE = ("<script>window.accountId = 11; window.gcSessionId = 22; window.accountUserId = 33;"
             "window.webinarWebsocketHosts = [\"ws1.example\",\"ws2.example\"]; window.webinarWebsocketPath = \"\\/ws3\\/webinar\";"
             "webinar.sign = 'abc123'; webinar.visitorId = '44'; webinar.id = 555; webinar.launchId = 1; webinar.subtype = 2;</script>")


class AutoInfo(unittest.TestCase):
    def test_values_are_read(self):
        i = vd.gc_auto_info(AUTO_PAGE)
        self.assertEqual((i["wid"], i["sign"], i["launch"], i["account"], i["session"], i["user"], i["visitor"]),
                         ("555", "abc123", "1", "11", "22", "33", "44"))
        self.assertEqual(i["hosts"], ["ws1.example", "ws2.example"])
        self.assertEqual(i["path"], "/ws3/webinar")

    def test_a_live_page_is_not_an_auto_webinar(self):
        self.assertEqual(vd.gc_auto_info(AUTO_PAGE.replace("subtype = 2", "subtype = 1")), {})
        self.assertEqual(vd.gc_auto_info(PAGE), {})

    def test_not_logged_in_has_its_own_message(self):
        with self.assertRaises(vd.RoomError) as c:
            vd.gc_auto_info(AUTO_PAGE.replace("window.accountUserId = 33;", ""))
        self.assertEqual(c.exception.key, "room_err_gc_page")

    def test_a_visitor_who_entered_by_name_only_may_connect(self):
        page = AUTO_PAGE.replace("accountUserId = 33", "accountUserId = -1")   # no account, no name form left
        self.assertEqual(vd.gc_auto_info(page)["user"], "-1")

    def test_a_visitor_who_has_not_given_a_name_yet_is_asked_to_enter(self):
        page = AUTO_PAGE.replace("accountUserId = 33", "accountUserId = -1") + '<input name="UserLite[name]">'
        with self.assertRaises(vd.RoomError) as c:
            vd.gc_auto_info(page)
        self.assertEqual(c.exception.key, "room_err_gc_page")

    def test_a_page_without_channel_values(self):
        with self.assertRaises(vd.RoomError) as c:
            vd.gc_auto_info("<script>webinar.subtype = 2;</script>")
        self.assertEqual(c.exception.key, "room_err_gc_nostream")


def _mask_read(sock):
    """One client frame's text (unmasked), or None."""
    try:
        b1, b2 = sock.recv(2)
    except (OSError, ValueError):
        return None
    n = b2 & 0x7F
    if n == 126:
        n = struct.unpack(">H", sock.recv(2))[0]
    mask = sock.recv(4)
    data = b""
    while len(data) < n:
        c = sock.recv(n - len(data))
        if not c:
            return None
        data += c
    return bytes(b ^ mask[i % 4] for i, b in enumerate(data)).decode()


class RecordingChannel:
    """A fake school channel: sends the handshake, then answers 'initAutoWebinar' with `replies`.
    Everything the client sends is kept in .got."""

    def __init__(self, replies, answer_after_init=True, connects_itself=False):
        import base64, hashlib, socket, time
        self.replies, self.got, self.connections, self.query = replies, [], 0, ""
        self.connects_itself = connects_itself
        self.sock = socket.socket(); self.sock.bind(("127.0.0.1", 0)); self.sock.listen(5)
        self.port = self.sock.getsockname()[1]
        self._b64, self._sha = base64, hashlib
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            try:
                c, _ = self.sock.accept()
            except OSError:
                return
            self.connections += 1
            threading.Thread(target=self._serve, args=(c,), daemon=True).start()

    def _serve(self, c):
        from test_room import ws_frame, OPEN
        try:
            head = b""
            while b"\r\n\r\n" not in head:
                head += c.recv(1)
            self.query = head.split(b"\r\n")[0].decode()
            key = [l.split(b": ")[1] for l in head.split(b"\r\n") if l.lower().startswith(b"sec-websocket-key")][0]
            acc = self._b64.b64encode(self._sha.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
            c.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                      b"Sec-WebSocket-Accept: " + acc + b"\r\n\r\n")
            c.sendall(ws_frame(OPEN))
            if self.connects_itself:                      # newer servers connect the namespace without being asked
                c.sendall(ws_frame("40"))
            while True:
                m = _mask_read(c)
                if m is None:
                    break
                self.got.append(m)
                if m.startswith('42["initAutoWebinar"'):
                    for r in self.replies:
                        c.sendall(ws_frame(r))
        except OSError:
            pass
        finally:
            c.close()

    def close(self):
        self.sock.close()


def video_event(hash_="h" * 32 + "/" + "k" * 32):
    return "42" + json.dumps(["update", {"channel": "public_auto_555_1", "actionType": 4,
                                         "url": "https://api.example/player/%s/master.m3u8?x=1" % hash_,
                                         "urlLive": "a" * 32, "videoTimestamp": 1794898200, "videoOffset": 171,
                                         "state": "webinar"}])


class AutoChannel(unittest.TestCase):
    def wait(self, ch, stop=None, **kw):
        info = vd.gc_auto_info(AUTO_PAGE)
        info["hosts"] = ["127.0.0.1:%d" % ch.port]
        return vd.gc_wait_for_video(info, "http://school.example", stop or threading.Event(),
                                    ws_url=lambda h: "ws://" + h, **kw)

    def test_video_message_gives_hash_start_and_offset(self):
        ch = RecordingChannel(['42["update",{"actionType":3,"status":"new"}]', video_event()])
        got = self.wait(ch)
        self.assertEqual(got, {"hash": "h" * 32 + "/" + "k" * 32, "start": 1794898200, "offset": 171})
        ch.close()

    def test_a_server_that_connects_by_itself_is_not_sent_a_second_connect(self):
        ch = RecordingChannel([video_event()], connects_itself=True)
        self.assertEqual(self.wait(ch)["start"], 1794898200)
        self.assertNotIn("40", ch.got)
        ch.close()

    def test_the_client_joins_the_channels_and_asks_for_the_state(self):
        ch = RecordingChannel([video_event()])
        self.wait(ch)
        joined = [json.loads(m[2:])[1]["channel"] for m in ch.got if m.startswith('42["join"')]
        self.assertEqual(joined, ["public_555", "public_555_1", "public_auto_555_1"])
        self.assertIn("40", ch.got)
        ask = [json.loads(m[2:]) for m in ch.got if m.startswith('42["initAutoWebinar"')][0]
        self.assertEqual(ask[1], {"id": 555, "launchNumber": "1"})
        for part in ("accountId=11", "sessionId=22", "webinarId=555", "userId=33", "sign=abc123", "launchId=1",
                     "visitorId=44", "EIO=3", "/ws3/webinar/"):
            self.assertIn(part, ch.query)
        ch.close()

    def test_stop_while_waiting(self):
        ch = RecordingChannel([])
        stop = threading.Event()
        threading.Timer(0.5, stop.set).start()
        self.assertIsNone(self.wait(ch, stop))
        ch.close()

    def test_gives_up_when_the_channel_never_opens(self):
        import socket
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()     # nothing listens
        info = vd.gc_auto_info(AUTO_PAGE); info["hosts"] = ["127.0.0.1:%d" % port]
        stop = threading.Event()
        stop.wait = lambda t=None: False            # no real sleeping in the test
        with self.assertRaises(vd.RoomError) as c:
            vd.gc_wait_for_video(info, "http://x", stop, ws_url=lambda h: "ws://" + h, reconnects=2)
        self.assertEqual(c.exception.key, "room_err_gc_socket")


MASTER = ("#EXTM3U\n"
          "#EXT-X-STREAM-INF:BANDWIDTH=1,RESOLUTION=640x360\nBASE/api/autoweb/get-media-playlist?jwt=J&h=360&host=e\n"
          "#EXT-X-STREAM-INF:BANDWIDTH=2,RESOLUTION=853x480\nBASE/api/autoweb/get-media-playlist?jwt=J&h=480&host=e\n"
          "#EXT-X-STREAM-INF:BANDWIDTH=3,RESOLUTION=1280x720\nBASE/api/autoweb/get-media-playlist?jwt=J&h=720&host=e\n")
VIDEO = {"hash": "h/k", "start": 5, "offset": 7}


class AutoSegments(unittest.TestCase):
    def fake(self, master_status=(200,), info=None):
        calls, seq = [], list(master_status)

        def get(url, headers):
            calls.append((url, dict(headers)))
            if "/pl/fileservice/api/aw-master" in url:
                return 200, b"/api/autoweb/get-master-playlist?jwt=J"
            if "get-master-playlist" in url:
                st = seq.pop(0) if len(seq) > 1 else seq[0]
                return st, MASTER.replace("BASE", "http://vh.example").encode() if st == 200 else b"busy"
            if "get-video-info" in url:
                return 200, json.dumps(info or {"status": "ok", "data": {"host": "edge.example", "urls": [
                    {"url": "/auwb/ts/a_0.ts?t=1", "dur": 3.08}, {"url": "/auwb/ts/a_1.ts?t=1", "dur": 3.0}]}}).encode()
            return 404, b""
        return get, calls

    def run_it(self, get, **kw):
        return vd.gc_auto_segments("https://school.example", VIDEO, "sid=1", threading.Event(),
                                   hosts=["http://vh.example"], get=get, pause=0, **kw)

    def test_segment_addresses_and_480p_choice(self):
        get, calls = self.fake()
        segs = self.run_it(get)
        self.assertEqual(segs, [("https://edge.example/auwb/ts/a_0.ts?t=1", 3.08), ("https://edge.example/auwb/ts/a_1.ts?t=1", 3.0)])
        info_call = [c for c in calls if "get-video-info" in c[0]][0][0]
        self.assertIn("h=480", info_call)

    def test_school_gets_the_login_and_the_values(self):
        get, calls = self.fake()
        self.run_it(get)
        first_url, first_hdr = calls[0]
        self.assertIn("hash=h%2Fk", first_url); self.assertIn("start=5", first_url); self.assertIn("timeoffset=7", first_url)
        self.assertEqual(first_hdr["Cookie"], "sid=1")
        self.assertEqual(first_hdr["Referer"], "https://school.example/")

    def test_server_that_takes_only_the_first_part_of_the_hash(self):
        """Found 2026-11-26: the school sends "<32>/<32>", the video server answers 500 to that and serves the
        first part alone."""
        ready, _ = self.fake()

        def get(url, headers):
            if "/pl/fileservice/api/aw-master" in url:
                jwt = b"TWO" if "hash=h%2Fk" in url else b"ONE"
                return 200, b"/api/autoweb/get-master-playlist?jwt=" + jwt
            if "get-master-playlist" in url and "jwt=TWO" in url:
                return 500, b""
            return ready(url, headers)
        self.assertEqual(len(self.run_it(get, attempts=2)), 2)

    def test_busy_master_server_is_retried(self):
        get, calls = self.fake(master_status=(503, 503, 200))
        self.run_it(get)
        self.assertEqual(len([c for c in calls if "get-master-playlist" in c[0]]), 3)

    def test_gives_up_with_its_own_message(self):
        get, _ = self.fake(master_status=(503,))
        with self.assertRaises(vd.RoomError) as c:
            self.run_it(get, attempts=3)
        self.assertEqual(c.exception.key, "room_err_gc_info")

    def test_empty_list_is_an_error(self):
        get, _ = self.fake(info={"status": "ok", "data": {"host": "e", "urls": []}})
        with self.assertRaises(vd.RoomError):
            self.run_it(get)

    def test_playlist_is_finished_and_parses_back(self):
        text = vd.gc_auto_playlist([("https://e/x0.ts?t=1", 3.08), ("https://e/x1.ts?t=1", 3.0)])
        pl = vd.hls_parse(text, vd.GC_AUTO_URL)
        self.assertTrue(pl["endlist"])
        self.assertEqual([(s[0], s[1], s[2]) for s in pl["segments"]], [(0, "https://e/x0.ts?t=1", 3.08), (1, "https://e/x1.ts?t=1", 3.0)])


class EnterSite(BaseHTTPRequestHandler):
    """A made-up school without passwords: a guest is sent to /enterweb_back (a form: name + e-mail);
    posting the form sets the cookie gcs=in, and then the webinar page knows the visitor."""
    posts = []
    mode = "ok"                      # ok | error | nocookie | otherhost | noform

    def log_message(self, *a): pass

    def _send(self, code, body, extra=()):
        b = body.encode()
        self.send_response(code); self.send_header("Content-Length", str(len(b)))
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        inside = "gcs=in" in (self.headers.get("Cookie") or "")
        if self.path.startswith("/enter-done"):
            self._send(200, "ok", [("Set-Cookie", "gcs=in; Path=/")])
            return
        if EnterSite.mode.startswith("lite") and not inside and self.path.startswith("/pl/webinar/show"):
            self._send(200, '<script>window.accountUserId = -1;</script><div class="webinar-login"><form id="w0" '
                       'action="/pl/webinar/show?id=7&amp;x=1" method="post"><input type="name" name="UserLite[name]">'
                       '<button type="submit">in</button></form></div>')
            return
        if self.path.startswith("/pl/webinar/show?id=8") or (inside and self.path.startswith("/pl/webinar/show")):
            self._send(200, "<script>window.accountUserId = 5;</script>" + PAGE)
        elif self.path.startswith("/pl/webinar/show"):
            self._send(302, "", [("Location", "/enterweb_back?utm_source=x")])
        elif self.path.startswith("/enterweb_back"):
            action = "https://other.example/pl/lite/block-public/process?id=9" if EnterSite.mode == "otherhost" \
                else "http://%s/pl/lite/block-public/process?id=9" % self.headers["Host"]
            form = ('<form id="f" action="%s" method="post">'
                    '<input type="hidden" name="formParams[willCreatePaidDeal]" value="0">'
                    '<input type="hidden" name="formParams[dealCustomFields][1]" value="utm-x">'
                    '<input type="text" name="formParams[full_name]" value="">'
                    '<input type="text" name="formParams[email]" value="">'
                    '<input type="text" name="formParams[phone]" value=""></form>' % action)
            flags = ('window.globalCheckboxEnabled = true; window.pdpCheckboxEnabled = true; '
                     'window.checkboxMailingEnabled = true; window.globalCheckboxForPaidOnly = false;'
                     if EnterSite.mode == "signed" else "window.globalCheckboxEnabled = false;")
            head = ('<script>window.accountUserId = -1; window.requestTime = 1700000000; '
                    'window.requestSimpleSign = "abc123def"; ' + flags + '</script>')
            self._send(200, head + ("" if EnterSite.mode == "noform" else form))
        else:
            self._send(404, "gone")

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        import urllib.parse as up
        EnterSite.posts.append({k: v[0] for k, v in up.parse_qs(self.rfile.read(n).decode()).items()})
        EnterSite.post_seen = (self.path, self.headers.get("X-Requested-With"))
        if EnterSite.mode == "lite":                          # a plain browser form: answer with a redirect and a cookie
            self._send(302, "", [("Location", self.path), ("Set-Cookie", "gcs=in; Path=/")])
            return
        if EnterSite.mode == "lite_stuck":
            self._send(302, "", [("Location", self.path)])
            return
        if EnterSite.mode == "error":
            self._send(200, json.dumps({"errorMessage": "Wrong data for anna@example.com"}))
        elif EnterSite.mode == "nocookie":
            self._send(200, json.dumps({"success": True}))
        elif EnterSite.mode == "signed":                    # like the real service: an unsigned form is not processed
            sent = EnterSite.posts[-1]
            if sent.get("requestSimpleSign") == "abc123def" and sent.get("globalConfirmCheckbox") == "on":
                self._send(200, json.dumps({"success": True, "data": {"formProcessed": True}}), [("Set-Cookie", "gcs=in; Path=/")])
            else:
                self._send(200, json.dumps({"success": True, "data": {"formProcessed": False}, "message": ""}))
        elif EnterSite.mode == "script":                    # the next page is named inside a script of the answer
            self._send(200, json.dumps({"success": True, "data": {"formProcessed": True, "preParts": [
                {"javascript": "window.location.href = '/enter-done';"}]}}))
        elif EnterSite.mode == "unprocessed":
            self._send(200, json.dumps({"success": True, "data": {"formProcessed": False}, "message": "Try again later"}))
        elif EnterSite.mode == "said":                      # accepted, a message instead of a login (a registration form)
            self._send(200, json.dumps({"success": True, "message": "",
                                        "data": {"defaultMessage": "<h3>Check your mail, Anna: anna@example.com</h3>"}}))
        elif EnterSite.mode == "refused":
            self._send(200, json.dumps({"success": False, "message": "Phone in international format", "data": []}))
        elif EnterSite.mode == "redirect":                  # the cookie is set only by the page the answer points to
            self._send(200, json.dumps({"success": True, "data": {"redirectUrl": "/enter-done"}}))
        else:
            self._send(200, json.dumps({"success": True}), [("Set-Cookie", "gcs=in; Path=/")])


class EnterRoom(unittest.TestCase):
    NAME, MAIL = "Anna Testova", "anna@example.com"

    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), EnterSite)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close()

    def setUp(self):
        import tempfile
        from unittest import mock
        EnterSite.posts = []; EnterSite.mode = "ok"
        self.tmp = tempfile.mkdtemp()
        p = mock.patch.object(vd, "LOGIN_DIR", self.tmp); p.start(); self.addCleanup(p.stop)

    def enter(self, pid=7):
        return vd.school_enter_room(f"{self.base}/pl/webinar/show?id={pid}&view=1", self.NAME, self.MAIL,
                                    timeout=5, allow_http=True)

    def test_form_is_posted_with_the_pages_own_fields_and_the_cookie_is_saved(self):
        path = self.enter()
        self.assertEqual(len(EnterSite.posts), 1)
        sent = EnterSite.posts[0]
        self.assertEqual(sent["formParams[full_name]"], self.NAME)
        self.assertEqual(sent["formParams[email]"], self.MAIL)
        self.assertEqual(sent["formParams[dealCustomFields][1]"], "utm-x")      # hidden field copied
        text = open(path, encoding="utf-8").read()
        self.assertIn("gcs\tin", text)
        self.assertNotIn(self.MAIL, text); self.assertNotIn(self.NAME, text)    # no personal data in the file
        self.assertTrue(path.startswith(self.tmp))

    def test_the_form_is_signed_and_ticked_like_the_browser_does(self):
        EnterSite.mode = "signed"
        self.enter()
        sent = EnterSite.posts[0]
        self.assertEqual((sent["requestTime"], sent["requestSimpleSign"]), ("1700000000", "abc123def"))
        self.assertTrue(sent["fromUrl"].endswith("/enterweb_back?utm_source=x"), sent["fromUrl"])
        self.assertEqual((sent["globalConfirmCheckbox"], sent["pdpConfirmCheckbox"]), ("on", "on"))
        self.assertFalse([k for k in sent if "mailing" in k.lower()])          # never signs up for advertising

    def test_a_school_without_consent_boxes_gets_none(self):
        self.enter()
        self.assertNotIn("globalConfirmCheckbox", EnterSite.posts[0])
        self.assertNotIn("pdpConfirmCheckbox", EnterSite.posts[0])

    def test_a_next_page_named_in_a_script_of_the_answer_is_visited(self):
        EnterSite.mode = "script"
        path = self.enter()
        self.assertIn("gcs\tin", open(path, encoding="utf-8").read())

    def test_an_unprocessed_form_is_a_failure_with_the_schools_words(self):
        EnterSite.mode = "unprocessed"
        with self.assertRaises(vd.LoginError) as c:
            self.enter()
        self.assertEqual((c.exception.args[0], c.exception.info), ("enter_err_fail", "Try again later"))

    def test_a_page_that_asks_only_for_a_name_is_entered_with_the_name_alone(self):
        EnterSite.mode = "lite"
        path = vd.school_enter_room(f"{self.base}/pl/webinar/show?id=7", self.NAME, "", timeout=5, allow_http=True)
        self.assertEqual(EnterSite.posts, [{"UserLite[name]": self.NAME}])          # nothing else leaves the PC
        self.assertEqual(EnterSite.post_seen, ("/pl/webinar/show?id=7&x=1", None))  # sent like a plain browser form
        text = open(path, encoding="utf-8").read()
        self.assertIn("gcs\tin", text)
        self.assertNotIn(self.NAME, text)

    def test_a_name_form_that_stays_on_the_page_is_a_failure(self):
        EnterSite.mode = "lite_stuck"
        with self.assertRaises(vd.LoginError) as c:
            vd.school_enter_room(f"{self.base}/pl/webinar/show?id=7", self.NAME, "", timeout=5, allow_http=True)
        self.assertEqual(c.exception.args[0], "enter_err_fail")
        self.assertNotIn(self.NAME, c.exception.info + c.exception.detail)
        self.assertFalse(os.listdir(self.tmp))

    def test_a_form_with_an_email_field_asks_for_the_email_before_anything_is_sent(self):
        with self.assertRaises(vd.LoginError) as c:
            vd.school_enter_room(f"{self.base}/pl/webinar/show?id=7", self.NAME, "", timeout=5, allow_http=True)
        self.assertEqual(c.exception.args[0], "enter_err_email")
        self.assertEqual(EnterSite.posts, [])

    def test_what_was_typed_is_only_ever_sent_encrypted_to_the_same_school(self):
        ok = vd.safe_school_address
        self.assertTrue(ok("https://school.example/x", "school.example", False))
        for bad in ("http://school.example/x", "https://other.example/x", "ftp://school.example/x"):
            self.assertFalse(ok(bad, "school.example", False), bad)
        self.assertTrue(ok("http://127.0.0.1:5/x", vd.host_of("http://127.0.0.1:5/y"), True))

    def test_a_redirect_to_another_host_is_not_followed(self):
        h = vd._SchoolRedirects("school.example", False)
        req = __import__("urllib.request").request.Request("https://school.example/a")
        for bad in ("https://other.example/b", "http://school.example/b"):
            with self.assertRaises(vd.LoginError):
                h.redirect_request(req, None, 302, "x", {}, bad)

    def test_a_phone_is_sent_only_into_a_phone_field(self):
        vd.school_enter_room(f"{self.base}/pl/webinar/show?id=7&view=1", self.NAME, self.MAIL, timeout=5, allow_http=True, phone="+100200300")
        self.assertEqual(EnterSite.posts[0]["formParams[phone]"], "+100200300")
        EnterSite.posts = []
        self.enter()                                                            # no phone given: the field is sent empty
        self.assertEqual(EnterSite.posts[0].get("formParams[phone]", ""), "")

    def test_the_page_named_in_the_answer_is_visited_to_make_the_entry_stick(self):
        EnterSite.mode = "redirect"
        path = self.enter()
        self.assertIn("gcs\tin", open(path, encoding="utf-8").read())

    def test_a_saved_password_login_is_not_overwritten(self):
        mine = os.path.join(self.tmp, "127.0.0.1.txt")           # what school_login writes for this host
        with open(mine, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\nPASSWORD-LOGIN\n")
        path = self.enter()
        self.assertNotEqual(os.path.realpath(path), os.path.realpath(mine))
        self.assertEqual(open(mine, encoding="utf-8").read(), "# Netscape HTTP Cookie File\nPASSWORD-LOGIN\n")
        self.assertTrue(os.path.isfile(path))

    def test_already_inside_posts_nothing(self):
        self.enter(pid=8)
        self.assertEqual(EnterSite.posts, [])

    def test_refusal_is_reported_without_the_users_data(self):
        EnterSite.mode = "error"
        with self.assertRaises(vd.LoginError) as c:
            self.enter()
        self.assertEqual(c.exception.args[0], "enter_err_fail")
        self.assertNotIn(self.MAIL, c.exception.info)

    def test_answer_ok_but_page_still_a_guest_is_a_failure(self):
        EnterSite.mode = "nocookie"
        with self.assertRaises(vd.LoginError) as c:
            self.enter()
        self.assertEqual(c.exception.args[0], "enter_err_registered")           # taken, but it did not log us in
        self.assertFalse(os.listdir(self.tmp))                                   # nothing saved

    def test_the_schools_own_words_are_shown_without_the_users_data(self):
        EnterSite.mode = "said"
        with self.assertRaises(vd.LoginError) as c:
            self.enter()
        self.assertEqual(c.exception.args[0], "enter_err_registered")
        self.assertIn("Check your mail", c.exception.info)
        for secret in (self.MAIL, "Anna", "Testova", "<h3>"):
            self.assertNotIn(secret, c.exception.info)
            self.assertNotIn(secret, c.exception.detail)
        self.assertIn("answer: data,message,success", c.exception.detail)       # for the helper's log

    def test_a_form_the_school_refuses_with_success_false_says_why(self):
        EnterSite.mode = "refused"
        with self.assertRaises(vd.LoginError) as c:
            self.enter()
        self.assertEqual(c.exception.args[0], "enter_err_fail")
        self.assertEqual(c.exception.info, "Phone in international format")

    def test_page_without_a_form(self):
        EnterSite.mode = "noform"
        with self.assertRaises(vd.LoginError) as c:
            self.enter()
        self.assertEqual(c.exception.args[0], "enter_err_form")

    def test_form_on_another_site_is_never_posted_to(self):
        EnterSite.mode = "otherhost"
        with self.assertRaises(vd.LoginError) as c:
            self.enter()
        self.assertEqual(c.exception.args[0], "login_err_site")
        self.assertEqual(EnterSite.posts, [])

    def test_plain_http_and_tricky_addresses_are_refused(self):
        for url, key in (("http://school.example/pl/webinar/show?id=1", "login_err_https"),
                         ("https://school.example@evil.example/x", "login_err_address")):
            with self.assertRaises(vd.LoginError) as c:
                vd.school_enter_room(url, self.NAME, self.MAIL)
            self.assertEqual(c.exception.args[0], key)


class Texts(unittest.TestCase):
    def test_the_consent_names_the_schools_boxes(self):
        self.assertIn("consent boxes", vd.T["en"]["enter_consent"])
        self.assertIn("галочки согласия", vd.T["ru"]["enter_consent"])

    def test_enter_room_texts_exist_in_both_languages(self):
        for key in ("enter_btn", "enter_title", "enter_help", "enter_site", "enter_name", "enter_email",
                    "enter_consent", "enter_go", "enter_busy", "enter_err_empty", "enter_err_form",
                    "enter_err_fail", "enter_err_registered", "enter_err_email", "enter_ok"):
            for lang in ("en", "ru"):
                self.assertIn(key, vd.T[lang], key)

    def test_auto_messages_exist_in_both_languages(self):
        for key in ("room_err_gc_socket", "room_err_gc_info"):
            for lang in ("en", "ru"):
                self.assertIn(key, vd.T[lang])

    def test_new_messages_exist_in_both_languages(self):
        for key in ("room_err_link", "room_err_gc_page", "room_err_gc_nostream"):
            for lang in ("en", "ru"):
                self.assertIn(key, vd.T[lang])
        self.assertIn("/pl/webinar/show", vd.T["en"]["room_err_link"])
        self.assertIn("/pl/webinar/show", vd.T["ru"]["room_err_link"])


class SchoolLiveStream(unittest.TestCase):
    """A school's live webinar through its video service (found 2026-11-20): viewer token on the page ->
    get-stream-info -> master playlist addresses. Fake service answers; nothing touches the network."""
    TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MX0.sig_-abc"
    ON_AIR = {"status": "ok", "isset_closed_tasks": False,
              "tasks": [{"task_id": "1", "process_id": "2", "playlists": ["https://a.example/m.m3u8?sign=x", "https://b.example/m.m3u8?sig=y"]}]}
    IDLE = {"status": "ok", "isset_closed_tasks": False, "tasks": []}
    OVER = {"status": "ok", "isset_closed_tasks": True, "tasks": []}

    @staticmethod
    def post_of(*answers):
        queue = list(answers)

        def post(url, fields):
            assert fields["jwt"] and url.endswith("/api/live-master-api/v1/get-stream-info")
            a = queue.pop(0) if len(queue) > 1 else queue[0]
            if isinstance(a, Exception):
                raise a
            return 200, json.dumps(a).encode()
        return post

    @staticmethod
    def get_ok(url):
        return b"#EXTM3U\n#EXT-X-VERSION:6\n"

    def test_the_viewer_token_is_read_from_the_page(self):
        page = "<script>videoBroadcastWidget.loadWebinarVideoByStreamJwt('%s');</script>" % self.TOKEN
        self.assertEqual(vd.gc_viewer_jwt(page), self.TOKEN)
        self.assertEqual(vd.gc_viewer_jwt("<html>no player here</html>"), "")

    def test_playlists_idle_and_ended(self):
        self.assertEqual(vd.gc_live_playlists(self.ON_AIR)[0][0], "https://a.example/m.m3u8?sign=x")
        self.assertEqual(vd.gc_live_playlists(self.IDLE), ([], False))
        self.assertEqual(vd.gc_live_playlists(self.OVER), ([], True))
        self.assertEqual(vd.gc_live_playlists({"tasks": [{"playlists": ["file:///etc/passwd", 5]}]}), ([], False))   # only http(s)

    def test_second_server_is_asked_when_the_first_fails(self):
        seen = []

        def post(url, fields):
            seen.append(url.split("/")[2])
            if len(seen) == 1:
                raise OSError("down")
            return 200, json.dumps(self.IDLE).encode()
        self.assertEqual(vd.gc_live_info(self.TOKEN, "https://s.example", post)["status"], "ok")
        self.assertEqual(seen, vd.GC_LIVE_API_HOSTS[:2])
        with self.assertRaises(vd.RoomError) as c:
            vd.gc_live_info(self.TOKEN, "https://s.example", lambda u, f: (550, b'{"status":"error"}'))
        self.assertEqual(c.exception.key, "room_err_gc_info")

    def test_waiting_until_the_broadcast_is_on_air(self):
        got = vd.gc_wait_for_live(self.TOKEN, "https://s.example", threading.Event(), poll=0.01,
                                  post=self.post_of(self.IDLE, self.IDLE, self.ON_AIR), get=self.get_ok)
        self.assertEqual(got, ("https://a.example/m.m3u8?sign=x", False))          # we were early: the beginning is not missing

    def test_a_broadcast_already_on_air_is_marked_as_a_late_start(self):
        got = vd.gc_wait_for_live(self.TOKEN, "https://s.example", threading.Event(), poll=0.01, post=self.post_of(self.ON_AIR), get=self.get_ok)
        self.assertEqual(got[1], True)

    def test_the_first_address_that_does_not_answer_is_skipped(self):
        def get(u):
            if "a.example" in u:
                raise OSError("404")
            return b"#EXTM3U"
        got = vd.gc_wait_for_live(self.TOKEN, "https://s.example", threading.Event(), poll=0.01, post=self.post_of(self.ON_AIR), get=get)
        self.assertEqual(got[0], "https://b.example/m.m3u8?sig=y")

    def test_stop_ends_the_wait(self):
        stop = threading.Event(); stop.set()
        self.assertIsNone(vd.gc_wait_for_live(self.TOKEN, "https://s.example", stop, post=self.post_of(self.IDLE), get=self.get_ok))

    def test_a_failed_service_answer_does_not_end_the_wait_but_five_in_a_row_do(self):
        calls = {"n": 0}

        def flaky(url, fields):
            calls["n"] += 1
            if calls["n"] <= 6:                       # 3 rounds x 2 hosts fail, then it works
                raise OSError("down")
            return 200, json.dumps(self.ON_AIR).encode()
        got = vd.gc_wait_for_live(self.TOKEN, "https://s.example", threading.Event(), poll=0.01, post=flaky, get=self.get_ok)
        self.assertEqual(got[0], "https://a.example/m.m3u8?sign=x")
        with self.assertRaises(vd.RoomError) as c:
            vd.gc_wait_for_live(self.TOKEN, "https://s.example", threading.Event(), poll=0.01,
                                post=lambda u, f: (500, b"{}"), get=self.get_ok)
        self.assertEqual(c.exception.key, "room_err_gc_info")

    def test_a_playlist_that_answers_late_does_not_hide_the_late_start(self):
        calls = {"n": 0}

        def get(u):
            calls["n"] += 1
            if calls["n"] <= 2:                       # both master addresses fail at the first look
                raise OSError("404")
            return b"#EXTM3U"
        got = vd.gc_wait_for_live(self.TOKEN, "https://s.example", threading.Event(), poll=0.01, post=self.post_of(self.ON_AIR), get=get)
        self.assertEqual(got[1], True)                # the service said "on air" at the first look: the beginning is missing

    def test_refresh_gives_a_fresh_address_or_reports_the_end(self):
        self.assertEqual(vd.gc_live_refresh(self.TOKEN, "https://s.example", self.post_of(self.ON_AIR), self.get_ok), "https://a.example/m.m3u8?sign=x")
        self.assertIsNone(vd.gc_live_refresh(self.TOKEN, "https://s.example", self.post_of(self.IDLE), self.get_ok))
        with self.assertRaises(vd.StreamOver):
            vd.gc_live_refresh(self.TOKEN, "https://s.example", self.post_of(self.OVER), self.get_ok)

    def test_the_form_is_sent_like_the_browser_does(self):
        seen = {}

        def fake_http(url, data=None, headers=None, timeout=30):
            seen.update(url=url, data=data, headers=headers)
            return 200, b"{}"
        old = vd._http
        vd._http = fake_http
        try:
            vd._post_form("https://x.example/api", {"jwt": "TOK"}, "https://s.example")
        finally:
            vd._http = old
        self.assertIn(b'name="jwt"\r\n\r\nTOK\r\n', seen["data"])
        self.assertTrue(seen["headers"]["Content-Type"].startswith("multipart/form-data; boundary="))
        self.assertEqual((seen["headers"]["Origin"], seen["headers"]["Referer"]), ("https://s.example", "https://s.example/"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
