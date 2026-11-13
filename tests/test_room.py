"""Offline tests for the webinar-room recorder (no internet, no real room).

    python tests\\test_room.py

Fake servers on 127.0.0.1 stand in for the room's web server and its Socket.IO
channel. Development only - not part of the release zip.
"""
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import tempfile
import threading
import time
import unittest
import http.server

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import VideoDownloader as vd  # noqa: E402


# ---------------------------------------------------------------- playlists
def playlist(first, count, endlist=False, dur=4.0, prefix="s"):
    lines = ["#EXTM3U", "#EXT-X-VERSION:3", "#EXT-X-TARGETDURATION:4",
             f"#EXT-X-MEDIA-SEQUENCE:{first}"]
    for i in range(first, first + count):
        lines += [f"#EXTINF:{dur},", f"{prefix}{i}.ts"]
    if endlist:
        lines.append("#EXT-X-ENDLIST")
    return "\n".join(lines) + "\n"


class FakeNet:
    """fetch(url) -> bytes. Playlist grows by `step` segments per playlist request."""

    def __init__(self, start=3, step=2, total=9, endlist=True, fail=()):
        self.n, self.step, self.total, self.endlist = start, step, total, endlist
        self.fail, self.calls = set(fail), 0

    def __call__(self, url):
        if url.endswith("live.m3u8"):
            self.calls += 1
            cur = min(self.n, self.total)
            self.n += self.step
            return playlist(0, cur, endlist=self.endlist and cur >= self.total).encode()
        name = url.rsplit("/", 1)[1]
        if name in self.fail:
            raise OSError("boom")
        return name.encode() + b"|"


URL = "https://cdn.example/stream/live.m3u8"


class PlaylistTests(unittest.TestCase):
    def test_parse_numbers_and_endlist(self):
        pl = vd.hls_parse(playlist(100, 3, endlist=True), URL)
        self.assertEqual([s[0] for s in pl["segments"]], [100, 101, 102])
        self.assertEqual(pl["segments"][0][1], "https://cdn.example/stream/s100.ts")
        self.assertEqual(sum(s[2] for s in pl["segments"]), 12.0)
        self.assertTrue(pl["endlist"])
        self.assertFalse(vd.hls_parse(playlist(0, 2), URL)["endlist"])

    def test_master_picks_highest_bandwidth(self):
        m = ("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360\nlow.m3u8\n"
             "#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720\nhigh.m3u8\n")
        self.assertEqual(vd.hls_best_variant(m, URL), "https://cdn.example/stream/high.m3u8")
        self.assertEqual(vd.hls_best_variant(playlist(0, 2), URL), "")

    def test_init_segment(self):
        t = '#EXTM3U\n#EXT-X-MAP:URI="init.mp4"\n#EXTINF:4,\na.m4s\n'
        self.assertEqual(vd.hls_parse(t, URL)["init"], "https://cdn.example/stream/init.mp4")


class SettingTests(unittest.TestCase):
    def test_direct_m3u8(self):
        self.assertEqual(vd.stream_from_setting("", "//a.example/x.m3u8?t=1"),
                         "https://a.example/x.m3u8?t=1")

    def test_rutube_balancer_and_live(self):
        vid = "0123456789abcdef0123456789abcdef"
        seen = []

        def fetch(u):
            seen.append(u)
            return json.dumps({"video_balancer": {"m3u8": "https://r.example/p.m3u8"}})
        self.assertEqual(vd.stream_from_setting("rutube", "https://rutube.ru/video/%s/" % vid, fetch),
                         "https://r.example/p.m3u8")
        self.assertIn(vid, seen[0])
        live = lambda u: json.dumps({"live_streams": {"hls": [{"url": "https://r.example/l.m3u8"}]}})
        self.assertEqual(vd.stream_from_setting("rutube", vid, live), "https://r.example/l.m3u8")
        self.assertEqual(vd.stream_from_setting("", vid, live), "https://r.example/l.m3u8")

    def test_rutube_without_address_and_other_types(self):
        with self.assertRaises(vd.RoomError) as c:
            vd.stream_from_setting("rutube", "https://rutube.ru/video/", lambda u: "{}")
        self.assertEqual(c.exception.key, "room_err_stream")
        with self.assertRaises(vd.RoomError) as c:
            vd.stream_from_setting("rutube", "0123456789abcdef0123456789abcdef", lambda u: "{}")
        self.assertEqual(c.exception.key, "room_err_stream")
        with self.assertRaises(vd.RoomError) as c:
            vd.stream_from_setting("vk", "video-1_2")
        self.assertEqual((c.exception.key, c.exception.info), ("room_err_type", {"vt": "vk"}))


class LinkTests(unittest.TestCase):
    def test_room_link(self):
        room, q = vd.room_split_link("https://online.example.ru/room/4-abc?username=A%20B&x=1")
        self.assertEqual(room, "https://online.example.ru/room/4-abc/")
        self.assertEqual(q["username"], "A B")

    def test_not_a_room_link(self):
        for bad in ("", "hello", "https://example.com/watch?v=1", "ftp://x/room/1"):
            with self.assertRaises(vd.RoomError, msg=bad) as c:
                vd.room_split_link(bad)
            self.assertEqual(c.exception.key, "room_err_link")


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.out = os.path.join(self.dir, "r.ts")

    def rec(self, net, stop=None, **kw):
        kw.setdefault("poll", 0.01); kw.setdefault("idle_end", 0.3); kw.setdefault("retries", 2)
        kw.setdefault("sleep", lambda s: time.sleep(0.005))
        return vd.RoomRecorder(URL, self.out, stop or threading.Event(), fetch=net, **kw)

    def data(self):
        with open(self.out, "rb") as f:
            return f.read()

    def test_whole_broadcast_in_order_until_endlist(self):
        res = self.rec(FakeNet(start=3, step=2, total=9)).run()
        self.assertEqual(res["reason"], "endlist")
        self.assertEqual((res["segments"], res["seconds"], res["failed"]), (9, 36.0, 0))
        self.assertEqual(self.data(), b"".join(b"s%d.ts|" % i for i in range(9)))

    def test_length_is_segments_times_four(self):
        res = self.rec(FakeNet(start=50, step=50, total=50)).run()
        self.assertEqual(res["seconds"], res["segments"] * 4.0)

    def test_stream_stops_without_endlist(self):
        res = self.rec(FakeNet(start=3, step=1, total=5, endlist=False)).run()
        self.assertEqual(res["reason"], "stalled")
        self.assertEqual(res["segments"], 5)

    def test_stop_button_saves_what_exists(self):
        stop = threading.Event()
        net = FakeNet(start=4, step=0, total=4, endlist=False)
        t = threading.Timer(0.15, stop.set); t.start()
        res = self.rec(net, stop, idle_end=30).run()
        self.assertEqual(res["reason"], "stopped")
        self.assertEqual(res["segments"], 4)

    def test_bad_segment_is_skipped_and_counted(self):
        res = self.rec(FakeNet(start=6, step=6, total=6, fail={"s2.ts"})).run()
        self.assertEqual((res["segments"], res["failed"]), (5, 1))
        self.assertNotIn(b"s2.ts", self.data())

    def test_playlist_that_slides_is_reported(self):
        msgs = []
        calls = {"n": 0}

        def net(url):
            if url.endswith("live.m3u8"):
                calls["n"] += 1
                return (playlist(0, 3) if calls["n"] == 1 else playlist(10, 3, endlist=True)).encode()
            return url.rsplit("/", 1)[1].encode() + b"|"
        res = self.rec(net, log=msgs.append).run()
        self.assertEqual(res["segments"], 6)
        self.assertTrue(any("skipped" in m for m in msgs))

    def test_master_playlist_is_followed(self):
        def net(url):
            if url.endswith("live.m3u8"):
                return b"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=5\nhi.m3u8\n"
            if url.endswith("hi.m3u8"):
                return playlist(0, 2, endlist=True).encode()
            return b"x"
        self.assertEqual(self.rec(net).run()["segments"], 2)

    def test_unreachable_playlist_gives_up(self):
        def net(url):
            raise OSError("down")
        res = self.rec(net, idle_end=0.1).run()
        self.assertEqual((res["reason"], res["segments"]), ("stalled", 0))

    def test_unique_path_never_overwrites(self):
        a = vd.unique_path(self.dir, "show", ".ts")
        open(a, "w").close()
        b = vd.unique_path(self.dir, "show", ".ts")
        self.assertNotEqual(a, b)
        self.assertTrue(b.endswith("show (2).ts"))

    def test_hms(self):
        self.assertEqual(vd.fmt_hms(7620), "2:07:00")
        self.assertEqual(vd.fmt_hms(59.9), "0:00:59")


# ---------------------------------------------------------------- fake room web server
class FakeRoom(http.server.BaseHTTPRequestHandler):
    log_message = lambda *a: None
    authorized = False
    quirk_seen = []

    def _send(self, code, body, ctype="text/html"):
        b = body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        if self.path.startswith("/room/r1/") and "Set-Cookie" not in self.headers:
            self.send_header("Set-Cookie", "sid=abc; Path=/")
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.headers.get("X-Requested-With"):       # the real room answers 404 here
            FakeRoom.quirk_seen.append(self.path); return self._send(404, "nope")
        if FakeRoom.authorized:
            return self._send(200, "<script>ssid: 'SS12345678'</script> room page")
        self._send(200, '<form name="login-form"></form><button id="btnLogin">')

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = self.rfile.read(n).decode()
        if not self.headers.get("X-Requested-With") or "/room/r1/" not in self.path:
            return self._send(404, "nope")
        if self.path.startswith("/room/r1/authorize"):
            FakeRoom.authorized = "username=&" not in body    # an empty name is refused
            return self._send(200, "{}", "application/json")
        if self.path.startswith("/room/r1/loadInitData"):
            return self._send(200, json.dumps({"ssid": "S", "ssign": "G", "roomid": "R",
                                               "groupid": "1", "ticketId": "T", "campid": "C"}),
                              "application/json")


class SignInTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeRoom)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_sign_in_returns_setup(self):
        FakeRoom.authorized = False
        room, init = vd.room_signin(self.base + "/room/r1?username=A&email=a%40b.c")
        self.assertEqual(room, self.base + "/room/r1/")
        self.assertEqual((init["roomid"], init["ssign"]), ("R", "G"))
        self.assertEqual(FakeRoom.quirk_seen, [])      # page requests carry no AJAX header

    def test_entry_form_means_closed(self):
        FakeRoom.authorized = False
        with self.assertRaises(vd.RoomError) as c:     # no username -> server keeps the form
            vd.room_signin(self.base + "/room/r1?x=1")
        self.assertEqual(c.exception.key, "room_err_closed")

    def test_unknown_room_is_refused(self):
        with self.assertRaises(vd.RoomError) as c:
            vd.room_signin(self.base + "/room/zzz?username=A")
        self.assertIn(c.exception.key, ("room_err_signin", "room_err_setup"))

    def test_server_down(self):
        with self.assertRaises(vd.RoomError) as c:
            vd.room_signin("http://127.0.0.1:1/room/r1?username=A")
        self.assertEqual(c.exception.key, "room_err_setup")


# ---------------------------------------------------------------- fake Socket.IO channel
def ws_frame(text):
    b = text.encode()
    h = bytes([0x81]) + (bytes([len(b)]) if len(b) < 126 else b"\x7e" + struct.pack(">H", len(b)))
    return h + b


class FakeChannel:
    """Accepts one WebSocket at a time and plays a script: list of text messages
    (or a float = pause in seconds). 'CLOSE' ends the connection."""

    def __init__(self, scripts):
        self.scripts, self.connections = list(scripts), 0
        self.sock = socket.socket(); self.sock.bind(("127.0.0.1", 0)); self.sock.listen(5)
        self.port = self.sock.getsockname()[1]
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            try:
                c, _ = self.sock.accept()
            except OSError:
                return
            self.connections += 1
            script = self.scripts.pop(0) if self.scripts else []
            threading.Thread(target=self._serve, args=(c, script), daemon=True).start()

    def _serve(self, c, script):
        try:
            head = b""
            while b"\r\n\r\n" not in head:
                head += c.recv(1)
            key = [l.split(b": ")[1] for l in head.split(b"\r\n") if l.lower().startswith(b"sec-websocket-key")][0]
            acc = base64.b64encode(hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
            c.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
                      b"Connection: Upgrade\r\nSec-WebSocket-Accept: " + acc + b"\r\n\r\n")
            for item in script:
                if item == "CLOSE":
                    break
                if isinstance(item, float):
                    time.sleep(item)
                else:
                    c.sendall(ws_frame(item))
            time.sleep(0.2)
        except OSError:
            pass
        finally:
            c.close()

    def close(self):
        self.sock.close()


OPEN = '0{"sid":"x","pingInterval":25000,"pingTimeout":5000}'


def ev(name, room):
    return "42" + json.dumps([name, {"room": room}])


class ChannelTests(unittest.TestCase):
    def wait(self, ch, stop=None, **kw):
        return vd.room_wait_for_stream({"ssid": "S"}, "http://127.0.0.1", stop or threading.Event(),
                                       ws_base="ws://127.0.0.1:%d" % ch.port, **kw)

    def test_returns_when_room_goes_on_air(self):
        ch = FakeChannel([[OPEN, "40", ev("welcome", {"online": False, "videoType": "rutube",
                                                      "hangoutsUrl": "", "title": "T"}),
                           '42["ontyping",{}]', 0.1,
                           ev("newsettings", {"online": True, "hangoutsUrl": "ID123"})]])
        got = self.wait(ch)
        self.assertEqual(got, ("rutube", "ID123", "T"))     # newsettings adds to welcome
        ch.close()

    def test_stop_while_waiting(self):
        ch = FakeChannel([[OPEN, "40", ev("welcome", {"online": False}), 2.0]])
        stop = threading.Event()
        threading.Timer(0.3, stop.set).start()
        t0 = time.time()
        self.assertIsNone(self.wait(ch, stop))
        self.assertLess(time.time() - t0, 3)
        ch.close()

    def test_reconnects_after_the_room_drops_the_channel(self):
        ch = FakeChannel([[OPEN, "40", "CLOSE"],
                          [OPEN, "40", ev("welcome", {"online": True, "videoType": "rutube",
                                                      "hangoutsUrl": "ID9"})]])
        stop = threading.Event()
        real_wait = stop.wait
        stop.wait = lambda t=None: real_wait(0.05)          # no real 3 s pause
        got = self.wait(ch, stop)
        self.assertEqual(got[1], "ID9")
        self.assertEqual(ch.connections, 2)
        ch.close()

    def test_gives_up_when_the_channel_never_opens(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        stop = threading.Event()
        stop.wait = lambda t=None: None                     # no real 3 s pauses in the test
        with self.assertRaises(vd.RoomError) as c:
            vd.room_wait_for_stream({"ssid": "S"}, "http://x", stop,
                                    ws_base="ws://127.0.0.1:%d" % port, reconnects=2)
        self.assertEqual(c.exception.key, "room_err_channel")

    def test_bad_first_message(self):
        ch = FakeChannel([["hello"]])
        stop = threading.Event()
        stop.wait = lambda t=None: None
        with self.assertRaises(vd.RoomError):
            self.wait(ch, stop, reconnects=0)
        ch.close()


class SafetyAndErrorTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def rec(self, out, net, stop=None, **kw):
        kw.setdefault("poll", 0.01); kw.setdefault("idle_end", 0.3); kw.setdefault("retries", 1)
        kw.setdefault("sleep", lambda s: time.sleep(0.005))
        return vd.RoomRecorder(URL, out, stop or threading.Event(), fetch=net, **kw)

    def test_room_link_needs_a_room_name(self):
        for bad in ("https://h.example/room", "https://h.example/room/", "https://h.example/rooms/x"):
            with self.assertRaises(vd.RoomError, msg=bad):
                vd.room_split_link(bad)
        self.assertEqual(vd.room_split_link("https://h.example/room/x")[0], "https://h.example/room/x/")

    def test_only_http_addresses_are_followed(self):
        pl = vd.hls_parse("#EXTM3U\n#EXTINF:4,\nfile:///C:/secret.ts\n#EXTINF:4,\nok.ts\n", URL)
        self.assertEqual([s[1] for s in pl["segments"]], ["https://cdn.example/stream/ok.ts"])
        with self.assertRaises(vd.RoomError):
            vd.stream_from_setting("", "file:///C:/x.m3u8")
        with self.assertRaises(OSError):
            vd._http("file:///C:/Windows/win.ini")

    def test_unwritable_folder_is_reported_as_disk_not_internet(self):
        res = self.rec(os.path.join(self.dir, "missing", "r.ts"), FakeNet()).run()
        self.assertEqual((res["reason"], res["segments"]), ("disk", 0))

    def test_disk_full_half_way_keeps_the_counts(self):
        class Full:
            n = 0
            def __init__(s, *a, **k): s.f = open(*a, **k)
            def __enter__(s): return s
            def __exit__(s, *a): s.f.close()
            def write(s, d):
                Full.n += 1
                if Full.n > 3:
                    raise OSError(28, "No space left on device")
                return s.f.write(d)
        vd.open = lambda *a, **k: Full(*a, **k)         # shadows the built-in inside the module
        try:
            res = self.rec(os.path.join(self.dir, "r.ts"), FakeNet(start=9, step=9, total=9)).run()
        finally:
            del vd.open
        self.assertEqual(res["reason"], "disk")
        self.assertEqual(res["segments"], 3)

    def test_stop_before_any_video(self):
        stop = threading.Event(); stop.set()
        res = self.rec(os.path.join(self.dir, "r.ts"), FakeNet(), stop).run()
        self.assertEqual((res["reason"], res["segments"]), ("stopped", 0))


class WordingTests(unittest.TestCase):
    def test_every_room_message_exists_in_both_languages(self):
        keys = {k for k in vd.T["en"] if k.startswith(("room_", "st_room_"))} | {"nav_room", "recording"}
        self.assertTrue(keys)
        for k in keys:
            self.assertIn(k, vd.T["ru"], k)
        for k in vd.T["ru"]:
            if k.startswith(("room_", "st_room_")):
                self.assertIn(k, vd.T["en"], k)

    def test_every_error_key_raised_has_wording(self):
        import re
        with open(vd.__file__, encoding="utf-8") as f:
            src = f.read()
        for key in set(re.findall(r'RoomError\("(\w+)"', src)):
            self.assertIn(key, vd.T["en"], key)
            self.assertIn(key, vd.T["ru"], key)


if __name__ == "__main__":
    unittest.main(verbosity=1)
