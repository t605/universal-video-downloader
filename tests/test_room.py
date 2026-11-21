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

    def test_master_picks_480p_like_every_download(self):
        # owner's rule 2026-11-20: recordings are 480p (a 3-hour webinar was 8 GB in 720p)
        m = ("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=400000,RESOLUTION=426x240\nlow.m3u8\n"
             "#EXT-X-STREAM-INF:BANDWIDTH=1100000,RESOLUTION=854x480\nmid.m3u8\n"
             "#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720\nhigh.m3u8\n"
             "#EXT-X-STREAM-INF:BANDWIDTH=6000000,RESOLUTION=1920x1080\nfull.m3u8\n")
        self.assertEqual(vd.hls_best_variant(m, URL), "https://cdn.example/stream/mid.m3u8")
        self.assertEqual(vd.hls_best_variant(playlist(0, 2), URL), "")

    def test_master_without_a_480p_stream(self):
        only_big = ("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=6000000,RESOLUTION=1920x1080\nfull.m3u8\n"
                    "#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720\nhigh.m3u8\n")
        self.assertEqual(vd.hls_best_variant(only_big, URL), "https://cdn.example/stream/high.m3u8")   # the lowest there is
        only_small = "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=300000,RESOLUTION=320x180\ntiny.m3u8\n"
        self.assertEqual(vd.hls_best_variant(only_small, URL), "https://cdn.example/stream/tiny.m3u8")

    def test_master_without_picture_sizes_goes_by_bandwidth(self):
        m = ("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=900000\na.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=1500000\nb.m3u8\n"
             "#EXT-X-STREAM-INF:BANDWIDTH=5000000\nc.m3u8\n")
        self.assertEqual(vd.hls_best_variant(m, URL), "https://cdn.example/stream/b.m3u8")
        big = "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=5000000\nc.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=3000000\nd.m3u8\n"
        self.assertEqual(vd.hls_best_variant(big, URL), "https://cdn.example/stream/d.m3u8")

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
            vd.stream_from_setting("bs", "video-1_2")
        self.assertEqual((c.exception.key, c.exception.info), ("room_err_type", {"vt": "bs"}))

    def test_vk_setting_goes_to_the_vk_resolver(self):
        seen = []
        got = vd.stream_from_setting("vk", "https://vk.com/video_ext.php?oid=-5&id=6&hash=x",
                                     vk_resolve=lambda r: seen.append(r) or "https://v.example/m.m3u8")
        self.assertEqual(got, "https://v.example/m.m3u8")
        self.assertIn("oid=-5", seen[0])
        # a VK address is recognised even when the room gives no type
        self.assertEqual(vd.stream_from_setting("", "https://vkvideo.ru/video-1_2",
                                                vk_resolve=lambda r: "https://v.example/n.m3u8"), "https://v.example/n.m3u8")

    def test_vk_page_url_forms(self):
        self.assertEqual(vd.vk_page_url("https://vk.com/video-1_2"), "https://vk.com/video-1_2")
        self.assertEqual(vd.vk_page_url("//vk.com/video_ext.php?oid=-7&amp;id=8"), "https://vk.com/video-7_8")
        self.assertEqual(vd.vk_page_url("https://x.example/p?oid=-7&id=8"), "https://vk.com/video-7_8")
        self.assertEqual(vd.vk_page_url("live-12_34"), "https://vk.com/video-12_34")
        self.assertEqual(vd.vk_page_url("-12_34"), "https://vk.com/video-12_34")
        self.assertEqual(vd.vk_page_url("vk: 456241533,-125375313,3,9dd2923c88225e87"),
                         "https://vk.com/video-125375313_456241533?hash=9dd2923c88225e87")
        self.assertEqual(vd.vk_page_url("nonsense"), "")

    def test_vk_player_page_address_keeps_its_hash_and_becomes_a_video_address(self):
        # what a room sent on 2026-11-20 for a running live broadcast (made-up ids): yt-dlp cannot read the
        # video_ext.php page ("Unable to extract player params") but reads /video<oid>_<id>?hash=..
        got = vd.vk_page_url("https://vk.ru/video_ext.php?oid=-77&id=88&js_api=1&hd=3&hash=f70abcdef0123456")
        self.assertEqual(got, "https://vk.com/video-77_88?hash=f70abcdef0123456")
        self.assertEqual(vd.vk_page_url("https://vk.com/video_ext.php?oid=-77&amp;id=88&amp;hash=ab12cd34ef56ab78"),
                         "https://vk.com/video-77_88?hash=ab12cd34ef56ab78")
        self.assertEqual(vd.vk_page_url("//vk.com/video_ext.php?oid=-7&id=8&hash=0123456789abcdef"),
                         "https://vk.com/video-7_8?hash=0123456789abcdef")
        self.assertEqual(vd.vk_page_url("https://vkvideo.ru/video_ext.php?oid=-7&id=8"), "https://vk.com/video-7_8")
        # any other VK address is passed on unchanged
        self.assertEqual(vd.vk_page_url("https://vkvideo.ru/video-7_8?hash=ab12"), "https://vkvideo.ru/video-7_8?hash=ab12")

    def test_vk_stream_url_picks_the_master_or_the_best_fitting_stream(self):
        import sys, types
        from unittest import mock
        def fake(info):
            class Y:
                def __init__(self, o): pass
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def extract_info(self, u, download=False): return info
            m = types.ModuleType("yt_dlp"); m.YoutubeDL = Y; return m
        info = {"formats": [{"url": "https://c.example/a.m3u8", "protocol": "m3u8_native", "height": 1080},
                            {"url": "https://c.example/b.m3u8", "protocol": "m3u8_native", "height": 480},
                            {"url": "https://c.example/x.mp4", "protocol": "https", "height": 720}]}
        with mock.patch.dict(sys.modules, {"yt_dlp": fake(info)}):
            self.assertEqual(vd.vk_stream_url("https://vk.com/video-1_2"), "https://c.example/b.m3u8")
        live = dict(info, is_live=True); vod = dict(info, is_live=False)
        with mock.patch.dict(sys.modules, {"yt_dlp": fake(live)}):               # still live: fine, also while recording
            self.assertEqual(vd.vk_stream_url("https://vk.com/video-1_2", live_only=True), "https://c.example/b.m3u8")
        with mock.patch.dict(sys.modules, {"yt_dlp": fake(vod)}):
            self.assertEqual(vd.vk_stream_url("https://vk.com/video-1_2"), "https://c.example/b.m3u8")   # a recorded video is fine
            with self.assertRaises(vd.StreamOver):                               # but while recording it means: the end
                vd.vk_stream_url("https://vk.com/video-1_2", live_only=True)
        big_only = {"formats": [{"url": "https://c.example/a.m3u8", "protocol": "m3u8_native", "height": 1080},
                                {"url": "https://c.example/c.m3u8", "protocol": "m3u8_native", "height": 720}]}
        with mock.patch.dict(sys.modules, {"yt_dlp": fake(big_only)}):          # nothing at 480p: the lowest there is
            self.assertEqual(vd.vk_stream_url("https://vk.com/video-1_2"), "https://c.example/c.m3u8")
        info["formats"][1]["manifest_url"] = "https://c.example/master.m3u8"
        with mock.patch.dict(sys.modules, {"yt_dlp": fake(info)}):
            self.assertEqual(vd.vk_stream_url("https://vk.com/video-1_2"), "https://c.example/master.m3u8")
        with mock.patch.dict(sys.modules, {"yt_dlp": fake({"formats": [{"url": "https://c.example/x.mp4"}]})}):
            with self.assertRaises(vd.RoomError) as c:
                vd.vk_stream_url("https://vk.com/video-1_2")
        self.assertEqual(c.exception.key, "room_err_vk")

    def _fake_yt(self, info=None, boom=False):
        import types

        class Y:
            def __init__(self, o): pass
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def extract_info(self, u, download=False):
                if boom:
                    raise RuntimeError("No video formats found!")
                return info
        m = types.ModuleType("yt_dlp"); m.YoutubeDL = Y
        return m

    def test_the_full_recording_is_taken_only_when_it_is_ready_and_longer(self):
        import sys
        from unittest import mock
        fmts = [{"url": "https://c.example/b.m3u8", "protocol": "m3u8_native", "height": 480}]
        cases = [
            (dict(formats=fmts, is_live=True, duration=None), None),          # still live
            (dict(formats=fmts, is_live=False, duration=100), None),          # not longer than what we have (100 + 30 needed)
            (dict(formats=fmts, is_live=False, duration=500), ("https://c.example/b.m3u8", 500)),
        ]
        for info, want in cases:
            with mock.patch.dict(sys.modules, {"yt_dlp": self._fake_yt(info)}):
                self.assertEqual(vd.vk_full_recording_url("https://vk.com/video-1_2", 100), want, info)
        with mock.patch.dict(sys.modules, {"yt_dlp": self._fake_yt(boom=True)}):   # VK is still processing the video
            self.assertIsNone(vd.vk_full_recording_url("https://vk.com/video-1_2", 100))

    def test_waiting_for_the_full_recording(self):
        answers = [None, None, ("https://c.example/full.m3u8", 9000)]
        calls, msgs = [], []

        def resolve(ref, secs):
            calls.append(secs)
            return answers.pop(0)
        got = vd.vk_wait_for_full("r", 100, threading.Event(), resolve=resolve, max_wait=5, interval=0.01, log=msgs.append)
        self.assertEqual(got, ("https://c.example/full.m3u8", 9000))
        self.assertEqual(calls, [100, 100, 100])
        self.assertTrue(any("published" in m for m in msgs))

    def test_waiting_for_the_full_recording_gives_up_and_can_be_stopped(self):
        msgs = []
        self.assertIsNone(vd.vk_wait_for_full("r", 100, threading.Event(), resolve=lambda r, s: None,
                                              max_wait=0.05, interval=0.02, log=msgs.append))
        self.assertTrue(any("did not publish" in m for m in msgs))
        stop = threading.Event(); stop.set()
        self.assertIsNone(vd.vk_wait_for_full("r", 100, stop, resolve=lambda r, s: ("u", 1), max_wait=5, interval=0.01))

    def test_a_lost_piece_needs_only_a_slightly_longer_video(self):
        import sys
        from unittest import mock
        fmts = [{"url": "https://c.example/b.m3u8", "protocol": "m3u8_native", "height": 480}]
        info = dict(formats=fmts, is_live=False, duration=104)               # 4 s longer than the 100 s recorded live
        with mock.patch.dict(sys.modules, {"yt_dlp": self._fake_yt(info)}):
            self.assertIsNone(vd.vk_full_recording_url("https://vk.com/video-1_2", 100))              # late start: needs +30 s
            self.assertEqual(vd.vk_full_recording_url("https://vk.com/video-1_2", 100, margin=1.0),
                             ("https://c.example/b.m3u8", 104))                                         # one piece lost only

    def test_the_wait_reports_the_time_waited_and_checks_every_three_minutes(self):
        import inspect
        self.assertEqual(inspect.signature(vd.vk_wait_for_full).parameters["interval"].default, 180.0)
        answers, seen = [None, None, ("u", 9000)], []
        vd.vk_wait_for_full("r", 100, threading.Event(), resolve=lambda r, s: answers.pop(0), max_wait=5, interval=0.01,
                            progress=lambda n, w: seen.append((n, w)))
        self.assertEqual([n for n, w in seen], [1, 2])                       # reported after each unsuccessful check
        self.assertTrue(all(w >= 0 for n, w in seen))

    def test_stale_hidden_download_folders_are_purged(self):
        import tempfile, os, time
        with tempfile.TemporaryDirectory() as d:
            old, new = os.path.join(d, ".vdl_old00000"), os.path.join(d, ".vdl_new00000")
            os.makedirs(old); os.makedirs(new)
            t = time.time() - 3 * 86400
            os.utime(old, (t, t))
            vd.run_into_free_names({"outtmpl": os.path.join(d, "x.%(ext)s")}, lambda o: None)
            self.assertFalse(os.path.exists(old))                            # a crashed download's leftovers
            self.assertTrue(os.path.exists(new))                             # a recent one may still be running

    def test_wait_texts_have_the_same_placeholders_in_both_languages(self):
        import string
        for key in ("st_room_wait_full", "st_room_getting_full", "st_room_done_late_nofull", "st_room_rec_late"):
            fields = [{f for _, f, _, _ in string.Formatter().parse(vd.T[l][key]) if f} for l in ("en", "ru")]
            self.assertEqual(fields[0], fields[1], key)
        self.assertEqual({f for _, f, _, _ in string.Formatter().parse(vd.T["en"]["st_room_wait_full"]) if f}, {"w", "r"})

    def test_vk_lookup_checks_certificates_like_the_rest_and_uses_only_vk_logins(self):
        import sys, types, tempfile, os
        from unittest import mock
        seen = []
        class Y:
            def __init__(self, o): seen.append(o)
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def extract_info(self, u, download=False):
                return {"formats": [{"url": "https://c.example/m.m3u8", "protocol": "m3u8_native"}]}
        m = types.ModuleType("yt_dlp"); m.YoutubeDL = Y
        d = tempfile.mkdtemp()
        school = os.path.join(d, "school.txt")
        with open(school, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\nschool.example\tFALSE\t/\tTRUE\t4102444800\tsid\tabc\n")
        with mock.patch.dict(sys.modules, {"yt_dlp": m}):
            vd.vk_stream_url("https://vk.com/video-1_2", school)
        self.assertIn("no-certifi", seen[0]["compat_opts"])
        self.assertNotIn("cookiefile", seen[0])          # a school's cookies are not handed to VK


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

    def test_an_expired_stream_address_is_renewed_and_the_recording_goes_on(self):
        # VK's address stops growing after ~30 minutes: the first playlist is stuck at 5 pieces, the renewed one goes on
        URL2 = "https://cdn.example/stream2/live.m3u8"

        def net(url):
            if url == URL:
                return playlist(0, 5).encode()
            if url == URL2:
                return playlist(0, 9, endlist=True).encode()
            return url.rsplit("/", 1)[1].encode() + b"|"
        asked, msgs = [], []
        res = self.rec(net, idle_end=3.0, refresh=lambda: asked.append(1) or URL2, refresh_stale=0.05,
                       log=msgs.append).run()
        self.assertEqual(res["reason"], "endlist")
        self.assertEqual((res["segments"], res["failed"]), (9, 0))
        self.assertEqual(self.data(), b"".join(b"s%d.ts|" % i for i in range(9)))     # in order, nothing twice
        self.assertGreaterEqual(len(asked), 1)
        self.assertTrue(any("renewed" in m for m in msgs))

    def test_pieces_dropped_by_a_sliding_playlist_are_counted(self):
        state = {"n": 0}

        def net(url):
            if url.endswith("live.m3u8"):
                state["n"] += 1
                return (playlist(0, 3) if state["n"] == 1 else playlist(10, 3, endlist=True)).encode()
            return url.rsplit("/", 1)[1].encode() + b"|"
        res = self.rec(net, idle_end=3.0).run()
        self.assertEqual((res["segments"], res["skipped"], res["reason"]), (6, 7, "endlist"))
        res2 = self.rec(FakeNet(start=3, step=2, total=9)).run()
        self.assertEqual(res2["skipped"], 0)

    def test_the_end_of_the_broadcast_reported_by_the_refresh_ends_the_recording_cleanly(self):
        def over():
            raise vd.StreamOver()
        msgs = []
        res = self.rec(FakeNet(start=3, step=1, total=5, endlist=False), idle_end=30.0, refresh=over,
                       refresh_stale=0.05, log=msgs.append).run()
        self.assertEqual((res["reason"], res["segments"], res["failed"]), ("ended", 5, 0))
        self.assertTrue(any("ended" in m for m in msgs))

    def test_short_pieces_are_polled_quickly_and_dropped_pieces_count_in_the_expected_length(self):
        r = self.rec(FakeNet(start=1, step=1, total=1), poll=4.0)
        self.assertEqual(r._poll_for(2.0), 1.0)                  # 2-second pieces: look every second
        self.assertEqual(r._poll_for(0.4), 0.5)                  # never faster than twice a second
        self.assertEqual(r._poll_for(10.0), 4.0)                 # long pieces keep the default
        self.assertEqual(r._poll_for(0.0), 4.0)
        self.assertEqual(vd.room_expected_seconds({"segments": 160, "seconds": 320.0, "skipped": 4}), 328.0)
        self.assertEqual(vd.room_expected_seconds({"segments": 0, "seconds": 0.0, "skipped": 3}), 0.0)

    def test_one_not_live_answer_is_not_the_end_but_two_in_a_row_are(self):
        answers = [vd.StreamOver, "ok", vd.StreamOver, vd.StreamOver]            # one transient answer, then a real end

        def refresh():
            a = answers.pop(0) if answers else vd.StreamOver
            if a is vd.StreamOver:
                raise vd.StreamOver()
            return URL
        msgs = []
        res = self.rec(FakeNet(start=3, step=1, total=5, endlist=False), idle_end=30.0, refresh=refresh,
                       refresh_stale=0.02, log=msgs.append).run()
        self.assertEqual(res["reason"], "ended")
        self.assertTrue(any("checking again" in m for m in msgs))                   # the first answer only made it check again

    def test_an_empty_renewal_answer_resets_the_count_of_finished_answers(self):
        r = self.rec(FakeNet(start=1, step=1, total=1))

        def over():
            raise vd.StreamOver()
        r.refresh = over
        r._renew("t")
        self.assertEqual(r._over_count, 1)
        r.refresh = lambda: None                      # the service shows nothing usable now: not a second "finished"
        r._renew("t")
        self.assertEqual(r._over_count, 0)
        r.refresh = over
        r._renew("t")
        self.assertFalse(r.over)

    def test_dropped_pieces_make_the_final_note_a_warning_and_keep_the_ts(self):
        import types
        me = types.SimpleNamespace()
        ok = {"seconds": 100.0, "failed": 0, "skipped": 0, "reason": "ended"}
        self.assertEqual(vd.App._room_done_note(me, ok, True, 100.0)[:2], ("ok", "st_room_done_kept"))
        gaps = dict(ok, skipped=4)
        self.assertEqual(vd.App._room_done_note(me, gaps, True, 100.0), ("warn", "st_room_done_skipped", {"n": 4}))
        both = dict(ok, failed=1, skipped=2)
        self.assertEqual(vd.App._room_done_note(me, both, True, 100.0)[2], {"n": 3})

    def test_a_slow_renewal_does_not_freeze_the_loop(self):
        r = self.rec(FakeNet(start=1, step=1, total=1), refresh_timeout=0.3)
        r.refresh = lambda: (time.sleep(3), URL)[1]
        t0 = time.time()
        self.assertFalse(r._renew("t"))
        self.assertLess(time.time() - t0, 1.5)
        r.refresh = lambda: URL
        self.assertTrue(r._renew("t"))                 # a quick answer still works

    def test_an_encrypted_stream_is_refused_and_leaves_no_data(self):
        enc = "#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI=\"k\"\n" + playlist(0, 3)
        self.assertTrue(vd.hls_parse(enc, URL)["encrypted"])
        self.assertFalse(vd.hls_parse("#EXT-X-KEY:METHOD=NONE\n" + playlist(0, 3), URL)["encrypted"])
        with self.assertRaises(vd.RoomError) as c:
            self.rec(lambda u: enc.encode()).run()
        self.assertEqual(c.exception.key, "room_err_enc")
        self.assertEqual(self.data(), b"")

    def test_a_renewed_address_that_restarts_its_numbering_does_not_stall_the_recording(self):
        URL2 = "https://cdn.example/stream2/live.m3u8"

        def net(url):
            if url == URL:
                return playlist(100, 5).encode()                       # pieces 100..104, then stuck
            if url == URL2:                                            # the new address numbers from 0 again and repeats 3 pieces
                return playlist(0, 8, endlist=True).encode()
            return url.rsplit("/", 1)[1].encode() + b"|"
        res = self.rec(net, idle_end=3.0, refresh=lambda: URL2, refresh_stale=0.05).run()
        self.assertEqual(res["reason"], "endlist")
        self.assertEqual(res["failed"], 0)
        self.assertGreaterEqual(res["segments"], 5)                    # the recording went on instead of waiting for number 105

    def test_stop_does_not_count_cut_short_pieces_as_failures(self):
        stop = threading.Event()

        def net(url):
            if url.endswith("live.m3u8"):
                return playlist(0, 6).encode()
            stop.set()                                                 # Stop pressed while pieces are being fetched
            raise OSError("network down")
        res = self.rec(net, stop, idle_end=30.0, retries=5).run()
        self.assertEqual(res["reason"], "stopped")
        self.assertEqual(res["failed"], 0)

    def test_an_odd_answer_while_waiting_for_vk_does_not_end_the_wait(self):
        answers = [RuntimeError("odd"), None, ("u", 9000)]

        def resolve(r, s):
            a = answers.pop(0)
            if isinstance(a, Exception):
                raise a
            return a
        self.assertEqual(vd.vk_wait_for_full("r", 100, threading.Event(), resolve=resolve, max_wait=5, interval=0.01),
                         ("u", 9000))

    def test_a_pause_in_the_broadcast_does_not_end_the_recording_when_the_idle_limit_is_long(self):
        # stuck for a while, then going on: with a long idle limit the recording waits and then carries on
        state = {"n": 0}

        def net(url):
            if url.endswith("live.m3u8"):
                state["n"] += 1
                if state["n"] < 40:                                  # the stream is paused at 3 pieces ...
                    return playlist(0, 3).encode()
                return playlist(0, 6, endlist=True).encode()         # ... and then goes on to the end
            return url.rsplit("/", 1)[1].encode() + b"|"
        res = self.rec(net, idle_end=30.0).run()
        self.assertEqual(res["reason"], "endlist")
        self.assertEqual(self.data(), b"".join(b"s%d.ts|" % i for i in range(6)))

    def test_the_address_is_also_renewed_on_a_timer_without_losing_or_doubling_pieces(self):
        asked = []
        res = self.rec(FakeNet(start=1, step=1, total=15), refresh=lambda: asked.append(1) or URL,
                       refresh_every=0.03, idle_end=3.0).run()
        self.assertEqual(res["reason"], "endlist")
        self.assertEqual(self.data(), b"".join(b"s%d.ts|" % i for i in range(15)))
        self.assertGreaterEqual(len(asked), 1)

    def test_a_failing_renewal_does_not_stop_the_recording(self):
        def boom():
            raise RuntimeError("VK says no")
        res = self.rec(FakeNet(start=3, step=1, total=5, endlist=False), refresh=boom, refresh_stale=0.05).run()
        self.assertEqual((res["reason"], res["segments"]), ("stalled", 5))

    def test_without_a_refresh_function_nothing_changes(self):
        res = self.rec(FakeNet(start=3, step=1, total=5, endlist=False)).run()
        self.assertEqual((res["reason"], res["segments"]), ("stalled", 5))

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
        self.assertTrue(b.endswith("show (1).ts"))

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

    def test_it_is_noted_when_the_broadcast_was_already_on_air_at_the_first_message(self):
        ch = FakeChannel([[OPEN, "40", ev("welcome", {"online": True, "videoType": "vk",
                                                      "hangoutsUrl": "vk: 1,-2,3,abcdef0123456789", "title": "T"})]])
        info = {}
        self.assertEqual(self.wait(ch, info=info)[0], "vk")
        self.assertTrue(info["on_air_at_join"])
        ch.close()

    def test_it_is_not_a_late_start_when_the_room_goes_on_air_while_we_wait(self):
        ch = FakeChannel([[OPEN, "40", ev("welcome", {"online": False, "videoType": "vk", "hangoutsUrl": "", "title": "T"}),
                           0.1, ev("newsettings", {"online": True, "hangoutsUrl": "vk: 1,-2,3,abcdef0123456789"})]])
        info = {}
        self.wait(ch, info=info)
        self.assertFalse(info["on_air_at_join"])
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
