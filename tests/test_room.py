"""Offline tests for the webinar-room recorder (no internet, no real room).

    python tests\\test_room.py

Fake servers on 127.0.0.1 stand in for the room's web server and its Socket.IO
channel. Development only - not part of the release zip.
"""
import base64
import hashlib
import json
import os
import re
import socket
import struct
import subprocess
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

    def test_a_missing_beginning_is_still_said_when_pieces_are_lost_too(self):
        import types
        late = types.SimpleNamespace(_late_start=True)
        ok = {"seconds": 100.0, "failed": 0, "skipped": 0, "reason": "ended"}
        for res, length_ok in ((dict(ok, skipped=4), True), (dict(ok, reason="stalled"), True), (ok, False)):
            self.assertEqual(vd.App._room_done_note(late, res, length_ok, 100.0)[:2], ("warn", "st_room_done_late_gaps"))
        self.assertEqual(vd.App._room_done_note(late, ok, True, 100.0)[:2], ("ok", "st_room_done_kept"))

    def test_every_finished_recording_message_starts_with_the_word_the_help_tells_her_to_wait_for(self):
        for key in vd.T["en"]:
            if key.startswith("st_room_done"):
                self.assertTrue(vd.T["en"][key].startswith("Done"), key)
                self.assertTrue(vd.T["ru"][key].startswith("Готово"), key)

    def test_a_partly_failed_list_download_is_a_warning_not_a_success(self):
        self.assertEqual(vd.App._batch_note(3, 0), ("ok", "st_done_n", {"ok": 3, "n": 3}))
        self.assertEqual(vd.App._batch_note(1, 2), ("warn", "st_done_part", {"ok": 1, "n": 3}))

    def test_a_slow_renewal_does_not_freeze_the_loop(self):
        r = self.rec(FakeNet(start=1, step=1, total=1), refresh_timeout=0.3)
        r.refresh = lambda: (time.sleep(3), URL)[1]
        t0 = time.time()
        self.assertFalse(r._renew("t"))
        self.assertLess(time.time() - t0, 1.5)
        r.refresh = lambda: URL
        self.assertTrue(r._renew("t"))                 # a quick answer still works

    def test_byte_range_pieces_are_read_and_fetched_with_a_range(self):
        pl = ('#EXTM3U\n#EXT-X-VERSION:6\n#EXT-X-MAP:URI="v.mp4",BYTERANGE="100@0"\n'
              '#EXTINF:4.0,\n#EXT-X-BYTERANGE:50@100\nv.mp4\n#EXTINF:4.0,\n#EXT-X-BYTERANGE:60\nv.mp4\n#EXT-X-ENDLIST\n')
        r = vd.hls_parse(pl, "https://cdn.example/dir/m.m3u8")
        self.assertEqual(r["init"], "https://cdn.example/dir/v.mp4#bytes=0-99")
        self.assertEqual([x[1] for x in r["segments"]], ["https://cdn.example/dir/v.mp4#bytes=100-149", "https://cdn.example/dir/v.mp4#bytes=150-209"])
        import http.server
        body = bytes(range(256)) * 4
        seen = []

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                rg = self.headers.get("Range")
                seen.append(rg)
                if self.path.startswith("/norange") or not rg:
                    self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
                    return
                a, b = [int(x) for x in rg.split("=")[1].split("-")]
                part = body[a:b + 1]
                self.send_response(206); self.send_header("Content-Length", str(len(part))); self.end_headers(); self.wfile.write(part)
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            base = "http://127.0.0.1:%d" % srv.server_address[1]
            self.assertEqual(vd._http(base + "/v.mp4#bytes=10-19"), (200, body[10:20]))
            self.assertEqual(seen[-1], "bytes=10-19")
            with self.assertRaises(OSError):                       # a server that sends the whole file for a range is refused
                vd._http(base + "/norange#bytes=10-19")
        finally:
            srv.shutdown(); srv.server_close()

    def test_a_kinescope_room_video_is_resolved_with_the_room_as_referer(self):
        calls = []
        old = vd.kinescope_stream
        vd.kinescope_stream = lambda u, ref, ctx=None: (calls.append((u, ref)) or ("https://cdn.example/master.m3u8?sign=x", "T"))
        try:
            for vt, ref in (("ks", "kinescope: AbCdEfGh1234567890JkLm"), ("kinescope", "https://kinescope.io/embed/AbCdEfGh1234567890JkLm")):
                self.assertEqual(vd.stream_from_setting(vt, ref, referer="https://room.example/"), "https://cdn.example/master.m3u8?sign=x")
            self.assertEqual(calls[0], ("https://kinescope.io/embed/AbCdEfGh1234567890JkLm", "https://room.example/"))
            vd.kinescope_stream = lambda u, ref, ctx=None: None
            with self.assertRaises(vd.RoomError):
                vd.stream_from_setting("ks", "kinescope: AbCdEfGh1234567890JkLm")
        finally:
            vd.kinescope_stream = old

    def test_name_and_email_are_put_into_a_room_link(self):
        out = vd.room_link_with("https://start.example/room/100001/demo?utm_source=x", "Anna Petrova", "anna@example.org")
        room, q = vd.room_split_link(out)
        self.assertEqual((room, q["username"], q["email"], q["utm_source"]), ("https://start.example/room/100001/demo/", "Anna Petrova", "anna@example.org", "x"))
        with self.assertRaises(vd.RoomError):
            vd.room_link_with("https://school.example/pl/webinar/show?id=5", "A", "a@b.c")

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


# ---------------------------------------------------------------- sound (a recording without sound is never "done")
SEPARATE = ('#EXTM3U\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",NAME="a",DEFAULT=YES,URI="a/audio.m3u8"\n'
            '#EXT-X-STREAM-INF:BANDWIDTH=900000,RESOLUTION=854x480,AUDIO="aud"\nv/video.m3u8\n')


class _RangeFiles(http.server.SimpleHTTPRequestHandler):
    """Files of one folder; a Range request gets exactly those bytes (as a video server does for EXT-X-BYTERANGE)."""
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            self.send_error(404)
            return
        with open(path, "rb") as f:
            body = f.read()
        rg = self.headers.get("Range")
        if rg:
            a, b = [int(x) for x in rg.split("=")[1].split("-")]
            body = body[a:b + 1]
        self.send_response(206 if rg else 200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _Prog:
    def set(self, v):
        pass


class _RoomApp:
    """The room worker of the real App, without a window: the real methods, the screen replaced by lists."""
    for _n in ("_room_worker_body", "_room_end", "_room_fail", "_room_progress", "_room_converting", "_room_done_note",
               "_room_clean_ts", "_media_seconds", "_has_audio", "_convert_worker", "_conv_done", "_conv_fail",
               "_conv_progress", "_room_net_wait", "_stop_room", "_stop_question"):
        if _n in vd.App.__dict__:
            locals()[_n] = vd.App.__dict__[_n]

    def __init__(self, folder):
        self._dl_dir, self._ffmpeg = folder, vd._find_ffmpeg()
        self._running, self._room_active, self._room_shown = True, True, 0.0
        self._room_stop, self._done_note, self._last_conv = threading.Event(), None, ""
        self._prog = _Prog()
        self.statuses, self.lines = [], []

    def after(self, ms, fn):
        fn()

    def _log(self, msg, tag="plain"):
        self.lines.append(msg)

    def _set_status(self, kind, key, action=None, sub="", **kw):
        self.statuses.append((kind, key))

    def _set_busy(self, *a, **k):
        pass

    def _room_buttons(self, *a, **k):
        pass

    def _cookie_file_for(self, url):
        return ""

    def _ssl_ctx(self):
        return None


@unittest.skipUnless(vd._find_ffmpeg(), "ffmpeg is not available")
class SoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.web = tempfile.mkdtemp()
        ff = vd._find_ffmpeg()
        hls = ["-f", "hls", "-hls_time", "4", "-hls_playlist_type", "vod"]
        picture = ["-f", "lavfi", "-i", "testsrc=size=160x120:rate=25"]
        tone = ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000"]
        h264 = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "50"]
        ranges = ["-hls_segment_type", "fmp4", "-hls_flags", "single_file"]      # byte ranges of one file, as Kinescope
        for sub, args, name in (("v", picture + ["-t", "12"] + h264 + hls + ranges, "video.m3u8"),
                                ("a", tone + ["-t", "12", "-c:a", "aac"] + hls + ranges, "audio.m3u8"),
                                ("m", picture + tone + ["-t", "12"] + h264 + ["-c:a", "aac"] + hls, "muxed.m3u8")):
            os.makedirs(os.path.join(cls.web, sub))
            subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y"] + args + [name],
                           cwd=os.path.join(cls.web, sub), check=True)
        cls._write("separate.m3u8", SEPARATE)
        cls._write("silent.m3u8", "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=900000,RESOLUTION=854x480\nv/video.m3u8\n")
        with open(os.path.join(cls.web, "v", "video.m3u8"), encoding="utf-8") as f:
            cls._write("v/live.m3u8", f.read().replace("#EXT-X-ENDLIST", ""))
        cls._write("live_separate.m3u8", SEPARATE.replace("v/video.m3u8", "v/live.m3u8"))
        with open(os.path.join(cls.web, "a", "audio.m3u8"), encoding="utf-8") as f:
            sound = f.read().splitlines()
        first = [i for i, l in enumerate(sound) if l.startswith("#EXTINF")][1]       # only the first piece of the sound
        cls._write("a/short.m3u8", "\n".join(sound[:first]) + "\n#EXT-X-ENDLIST\n")
        cls._write("a/locked.m3u8", "\n".join(sound).replace("#EXTM3U", '#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="k"') + "\n")
        cls._write("short_sound.m3u8", SEPARATE.replace("a/audio.m3u8", "a/short.m3u8"))
        cls._write("locked_sound.m3u8", SEPARATE.replace("a/audio.m3u8", "a/locked.m3u8"))
        web = cls.web
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), lambda *a, **k: _RangeFiles(*a, directory=web, **k))
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = "http://127.0.0.1:%d/" % cls.srv.server_address[1]

    @classmethod
    def _write(cls, name, text):
        with open(os.path.join(cls.web, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close()

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.saved = {n: getattr(vd, n) for n in ("room_signin", "room_wait_for_stream", "stream_from_setting", "vk_wait_for_full")}

    def tearDown(self):
        for n, f in self.saved.items():
            setattr(vd, n, f)

    def record(self, vt, playlist_name, on_air=False):
        def wait(init, origin, stop, info=None, **kw):
            if info is not None:
                info["on_air_at_join"] = on_air
            return vt, "kinescope: abcdefghij123", "Lesson"
        vd.room_signin = lambda link: ("https://start.example/room/1/x/", {})
        vd.room_wait_for_stream = wait
        vd.stream_from_setting = lambda *a, **k: self.base + playlist_name
        app = _RoomApp(self.dir)
        app._room_worker_body("https://start.example/room/1/x", app._room_stop)
        return app

    def files(self, ext):
        return sorted(f for f in os.listdir(self.dir) if f.lower().endswith(ext))

    def streams(self, name):
        r = subprocess.run([vd._find_ffmpeg(), "-hide_banner", "-i", os.path.join(self.dir, name)],
                           capture_output=True, text=True, errors="replace")
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
        secs = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0
        return "Video:" in r.stderr, "Audio:" in r.stderr, secs

    def test_a_kinescope_room_with_a_separate_sound_track_gives_one_mp4_with_picture_and_sound(self):
        app = self.record("ks", "separate.m3u8")
        self.assertEqual(self.files(".mp4"), ["Lesson.mp4"], app.lines)
        video, audio, secs = self.streams("Lesson.mp4")
        self.assertEqual((video, audio), (True, True), app.lines)
        self.assertAlmostEqual(secs, 12.0, delta=0.6)
        self.assertEqual(self.files(".ts"), [], app.lines)               # nothing confusing is left beside the MP4
        self.assertEqual(app.statuses[-1], ("ok", "st_room_done"))

    def test_a_video_without_sound_is_never_done_and_the_ts_is_kept(self):
        app = self.record("ks", "silent.m3u8")
        self.assertEqual(app.statuses[-1], ("warn", "st_room_done_noaudio"), app.lines)
        self.assertEqual(self.files(".ts"), ["Lesson.ts"])

    def test_a_running_broadcast_with_a_separate_sound_track_is_refused_with_a_clear_message(self):
        app = self.record("ks", "live_separate.m3u8")
        self.assertEqual(app.statuses[-1], ("err", "room_err_audio"), app.lines)
        self.assertEqual(self.files(".mp4"), [])

    def test_a_sound_track_much_shorter_than_the_picture_is_a_warning_and_keeps_the_files(self):
        app = self.record("ks", "short_sound.m3u8")
        self.assertEqual(app.statuses[-1], ("warn", "st_room_done_check"), app.lines)
        self.assertEqual(self.files(".ts"), ["Lesson (sound).ts", "Lesson.ts"])

    def test_an_encrypted_sound_track_leaves_no_files_behind(self):
        app = self.record("ks", "locked_sound.m3u8")
        self.assertEqual(app.statuses[-1], ("err", "room_err_enc"), app.lines)
        self.assertEqual(self.files(".ts"), [])

    def test_the_missing_beginning_is_said_even_if_the_ts_cannot_be_removed(self):
        ts, mp4 = os.path.join(self.dir, "r.ts"), os.path.join(self.dir, "r.mp4")
        ff = vd._find_ffmpeg()
        for out in (ts, mp4):
            subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", os.path.join(self.web, "m", "muxed.m3u8"),
                            "-c", "copy", out], check=True)
        app = _RoomApp(self.dir)
        app._late_start, app._wait_nofull = True, False
        app._done_note = ("ok", "st_room_done_kept", {"t": "0:00:12"})
        old = vd.os.remove

        def locked(p):
            raise OSError("in use")
        vd.os.remove = locked
        try:
            app._room_clean_ts(ts, mp4, lambda *a: None)
        finally:
            vd.os.remove = old
        self.assertEqual(app._done_note[:2], ("warn", "st_room_done_late"))

    def test_a_silent_full_recording_from_vk_never_replaces_the_live_recording_with_sound(self):
        vd.vk_wait_for_full = lambda *a, **k: (self.base + "v/video.m3u8", "full")
        app = self.record("vk", "m/muxed.m3u8", on_air=True)
        self.assertEqual(self.files(".mp4"), ["Lesson.mp4"], app.lines)
        self.assertTrue(self.streams("Lesson.mp4")[1], app.lines)        # the sound of the live recording survived
        self.assertEqual(app.statuses[-1][0], "warn")


class SeparateSoundPlaylistTests(unittest.TestCase):
    def test_the_sound_track_of_a_variant_is_found(self):
        base = "https://cdn.example/d/master.m3u8"
        self.assertEqual(vd.hls_variant_audio(SEPARATE, base, "https://cdn.example/d/v/video.m3u8"),
                         "https://cdn.example/d/a/audio.m3u8")
        muxed = ('#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",NAME="a"\n'
                 '#EXT-X-STREAM-INF:BANDWIDTH=1,RESOLUTION=854x480,AUDIO="aud"\nv.m3u8\n')     # no URI: sound is inside
        self.assertEqual(vd.hls_variant_audio(muxed, base, "https://cdn.example/d/v.m3u8"), "")

    def test_a_sound_only_stream_is_never_taken_instead_of_the_picture(self):
        master = SEPARATE + '#EXT-X-STREAM-INF:BANDWIDTH=64000,CODECS="mp4a.40.2"\nonly_sound.m3u8\n'
        self.assertEqual(vd.hls_best_variant(master, "https://cdn.example/d/master.m3u8", muxed_only=True), "")

    def test_a_group_whose_main_sound_is_inside_the_picture_is_not_separate(self):
        base = "https://cdn.example/d/master.m3u8"
        master = ('#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",NAME="main",DEFAULT=YES\n'
                  '#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",NAME="other language",URI="other.m3u8"\n'
                  '#EXT-X-STREAM-INF:BANDWIDTH=1,RESOLUTION=854x480,AUDIO="aud"\nv.m3u8\n')
        self.assertEqual(vd.hls_variant_audio(master, base, "https://cdn.example/d/v.m3u8"), "")

    def test_the_sound_file_belongs_to_its_picture_file_by_name(self):
        d = tempfile.mkdtemp()
        for name in ("Lesson (1).ts", "Lesson (1) (sound).ts", "Other.ts"):
            open(os.path.join(d, name), "w").close()
        self.assertEqual(vd.sound_beside(os.path.join(d, "Lesson (1).ts")), os.path.join(d, "Lesson (1) (sound).ts"))
        self.assertEqual(vd.sound_beside(os.path.join(d, "Other.ts")), "")
        self.assertEqual(vd.sound_beside(os.path.join(d, "Lesson (1).mp4")), "")      # only the raw recording has a partner

    def test_the_recorder_prefers_a_stream_with_the_sound_inside(self):
        master = SEPARATE + "#EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=640x360\nm/muxed.m3u8\n"
        asked = []

        def fetch(u):
            asked.append(u.rsplit("/", 1)[-1])
            if u.endswith("master.m3u8"):
                return master.encode()
            return playlist(0, 2, endlist=True).encode() if u.endswith(".m3u8") else b"x"
        out = os.path.join(tempfile.mkdtemp(), "r.ts")
        res = vd.RoomRecorder("https://cdn.example/d/master.m3u8", out, threading.Event(), fetch=fetch, poll=0.01).run()
        self.assertEqual(res["reason"], "endlist")
        self.assertIn("muxed.m3u8", asked)
        self.assertNotIn("video.m3u8", asked)


# ---------------------------------------------------------------- a broken connection must not leave holes in a ready recording
class _Net:
    """A finished playlist of `total` pieces; `broken(name, n)` returns the error to raise on the n-th request, or None."""

    def __init__(self, total, broken, endlist=True, init=False):
        self.total, self.broken, self.endlist, self.init = total, broken, endlist, init
        self.asked = {}

    def __call__(self, url):
        if url.endswith("live.m3u8"):
            text = playlist(0, self.total, endlist=self.endlist)
            if self.init:
                text = text.replace("#EXTM3U", '#EXTM3U\n#EXT-X-MAP:URI="init.mp4"')
            return text.encode()
        name = url.rsplit("/", 1)[1]
        self.asked[name] = self.asked.get(name, 0) + 1
        err = self.broken(name, self.asked[name])
        if err:
            raise err
        return name.encode() + b"|"


class NetworkBreakTests(unittest.TestCase):
    def setUp(self):
        self.out = os.path.join(tempfile.mkdtemp(), "r.ts")

    def rec(self, net, stop=None, **kw):
        kw.setdefault("poll", 0.01); kw.setdefault("idle_end", 0.3); kw.setdefault("retries", 2)
        kw.setdefault("sleep", lambda s: time.sleep(0.005)); kw.setdefault("outage_wait", 5.0)
        return vd.RoomRecorder(URL, self.out, stop or threading.Event(), fetch=net, **kw)

    def data(self):
        with open(self.out, "rb") as f:
            return f.read()

    def whole(self, n):
        return b"".join(b"s%d.ts|" % i for i in range(n))

    def test_a_ready_recording_waits_for_the_connection_and_has_no_holes(self):
        down = lambda name, n: ConnectionError("network down") if name != "s0.ts" and n <= 12 else None
        waits = []
        res = self.rec(_Net(6, down), waiting=waits.append).run()
        self.assertEqual((res["reason"], res["segments"], res["failed"]), ("endlist", 6, 0))
        self.assertEqual(self.data(), self.whole(6))
        self.assertEqual(waits[:2], [True, False])                  # the screen is told, and told again when it is back

    def test_a_piece_the_server_refuses_is_not_waited_for(self):
        gone = lambda name, n: vd.HttpStatusError(404) if name == "s2.ts" else None
        waits = []
        t0 = time.time()
        res = self.rec(_Net(6, gone), waiting=waits.append, outage_wait=30.0).run()
        self.assertEqual((res["segments"], res["failed"]), (5, 1))
        self.assertEqual(waits, [])
        self.assertLess(time.time() - t0, 5.0)

    def test_a_server_that_is_briefly_unavailable_is_waited_for(self):
        busy = lambda name, n: vd.HttpStatusError(503) if name == "s2.ts" and n <= 6 else None
        res = self.rec(_Net(4, busy)).run()
        self.assertEqual((res["segments"], res["failed"]), (4, 0))

    def test_a_connection_that_never_returns_is_given_up_once_not_for_every_piece(self):
        down = lambda name, n: ConnectionError("down") if name != "s0.ts" else None
        waits = []
        t0 = time.time()
        res = self.rec(_Net(12, down), waiting=waits.append, outage_wait=0.4).run()
        self.assertEqual((res["reason"], res["segments"], res["failed"]), ("lost", 1, 1))
        self.assertEqual(waits, [True, False])
        self.assertLess(time.time() - t0, 4.0)

    def test_a_piece_the_server_keeps_failing_is_given_up_soon_and_the_rest_is_saved(self):
        broken = lambda name, n: vd.HttpStatusError(500) if name in ("s2.ts", "s5.ts", "s8.ts") else None
        t0 = time.time()
        res = self.rec(_Net(12, broken), outage_wait=60.0, server_wait=0.2, server_budget=0.5).run()
        self.assertEqual((res["reason"], res["segments"], res["failed"]), ("endlist", 9, 3))
        self.assertLess(time.time() - t0, 5.0)

    def test_after_giving_up_no_further_piece_is_asked_for(self):
        down = lambda name, n: ConnectionError("down") if name != "s0.ts" else None
        net = _Net(200, down)                                     # many batches: 200 pieces, 2 workers
        res = self.rec(net, outage_wait=0.3, workers=2).run()
        self.assertEqual((res["reason"], res["segments"], res["failed"]), ("lost", 1, 1))
        self.assertLessEqual(len(net.asked), 4)                   # only the batch in which it gave up
        self.assertEqual(self.data(), self.whole(1))

    def test_a_long_outage_does_not_use_up_the_patience_for_server_errors(self):
        def broken(name, n):
            if name == "s1.ts" and n <= 8:
                return ConnectionError("down")
            if name == "s1.ts" and n == 9:
                return vd.HttpStatusError(503)                    # the first answer when the connection is back
            return None
        slow = lambda s: time.sleep(0.05)
        res = self.rec(_Net(3, broken), sleep=slow, outage_wait=30.0, server_wait=1.0, server_budget=0.2).run()
        self.assertEqual((res["segments"], res["failed"]), (3, 0))

    def test_the_length_of_a_finished_playlist_is_reported(self):
        self.assertEqual(self.rec(_Net(3, lambda *a: None)).run()["total"], 12.0)

    def test_stop_while_waiting_saves_the_unbroken_part_only(self):
        stop = threading.Event()
        down = lambda name, n: ConnectionError("down") if name == "s2.ts" else None
        res = self.rec(_Net(6, down), stop, outage_wait=30.0,
                       waiting=lambda on: stop.set() if on else None).run()
        self.assertEqual((res["reason"], res["segments"], res["failed"]), ("stopped", 2, 0))
        self.assertEqual(self.data(), self.whole(2))                # nothing is written after the gap

    def test_a_running_broadcast_does_not_wait_for_a_lost_piece(self):
        down = lambda name, n: ConnectionError("down") if name == "s2.ts" else None
        waits = []
        res = self.rec(_Net(6, down, endlist=False), waiting=waits.append, outage_wait=30.0).run()
        self.assertEqual((res["segments"], res["failed"], waits), (5, 1, []))

    def test_a_first_piece_that_cannot_be_read_stops_the_recording_with_an_error(self):
        gone = lambda name, n: vd.HttpStatusError(404) if name == "init.mp4" else None
        with self.assertRaises(vd.RoomError) as cm:
            self.rec(_Net(3, gone, init=True)).run()
        self.assertEqual(cm.exception.key, "room_err_stream")

    def test_a_first_piece_is_waited_for_like_any_other(self):
        down = lambda name, n: ConnectionError("down") if name == "init.mp4" and n <= 5 else None
        res = self.rec(_Net(2, down, init=True)).run()
        self.assertEqual((res["segments"], res["failed"]), (2, 0))
        self.assertTrue(self.data().startswith(b"init.mp4|"))

    def test_a_byte_range_answered_with_too_few_bytes_is_not_accepted(self):
        class Short(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                self.send_response(206); self.send_header("Content-Length", "3"); self.end_headers()
                self.wfile.write(b"abc")
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Short)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            url = "http://127.0.0.1:%d/f#bytes=0-9" % srv.server_address[1]
            with self.assertRaises(ConnectionError):
                vd._http(url)
            self.assertEqual(vd._http(url.replace("0-9", "0-2")), (200, b"abc"))
        finally:
            srv.shutdown(); srv.server_close()


class HonestStopMessages(unittest.TestCase):
    def note(self, res, **state):
        import types
        return vd.App._room_done_note(types.SimpleNamespace(**state), res, True, res["seconds"])

    def test_a_ready_recording_that_was_cut_short_is_never_a_plain_success(self):
        res = {"seconds": 20.0, "failed": 0, "skipped": 0, "reason": "stopped"}
        self.assertEqual(self.note(res, _room_vod_total=60.0)[:2], ("warn", "st_room_done_cut"))
        self.assertEqual(self.note(dict(res, reason="lost", failed=1), _room_vod_total=60.0)[:2], ("warn", "st_room_done_cut"))
        whole = dict(res, seconds=60.0)
        self.assertEqual(self.note(whole, _room_vod_total=60.0)[0], "ok")

    def test_the_length_known_by_the_recorder_counts_too_and_a_late_start_stays_said(self):
        res = {"seconds": 20.0, "failed": 0, "skipped": 0, "reason": "stopped", "total": 60.0}
        self.assertEqual(self.note(res)[:2], ("warn", "st_room_done_cut"))
        lost = dict(res, reason="lost", failed=1)
        self.assertEqual(self.note(lost, _late_start=True)[:2], ("warn", "st_room_done_late_gaps"))

    def test_new_final_messages_exist(self):
        for key in ("st_room_done_cut", "st_room_done_stopped", "room_stop_ask_sound", "room_stop_ask_full"):
            for lang in ("en", "ru"):
                self.assertIn(key, vd.T[lang], key)


class ClosingAndStopping(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_closing_during_a_conversion_does_not_start_a_second_pass(self):
        app = _RoomApp(self.dir)
        started = []

        class Killed:
            stdout = iter(())

            def __init__(p, cmd, **k):
                if "-progress" not in cmd:
                    raise OSError("the length probe is not part of this test")
                started.append(cmd)
                app._closing = True                       # the window is closed while ffmpeg runs: it is killed

            def wait(p):
                return 1
        old = vd.subprocess.Popen
        vd.subprocess.Popen = Killed
        app._ffmpeg = sys.executable                       # only the length probe really runs; it fails harmlessly
        try:
            app._convert_worker(os.path.join(self.dir, "r.ts"), os.path.join(self.dir, "r.mp4"))
        finally:
            vd.subprocess.Popen = old
        self.assertEqual(len(started), 1)
        self.assertEqual(app.statuses, [])                 # nothing is written to a window that is gone

    def stop_with(self, answer, **state):
        app = _RoomApp(self.dir)
        app._waiting_full = False
        for k, v in state.items():
            setattr(app, k, v)
        asked = []
        old = vd.messagebox.askyesno
        app.t = lambda key, **kw: key
        vd.messagebox.askyesno = lambda title, text, **k: asked.append((text, k.get("default"))) or answer
        try:
            app._stop_room()
        finally:
            vd.messagebox.askyesno = old
        return app, asked

    def test_stop_during_a_recording_asks_first_and_no_keeps_recording(self):
        app, asked = self.stop_with(False, _rec_started=True)
        self.assertEqual(asked, [("room_stop_ask", "no")])
        self.assertFalse(app._room_stop.is_set())

    def test_stop_during_a_recording_stops_after_yes(self):
        app, asked = self.stop_with(True, _rec_started=True)
        self.assertTrue(app._room_stop.is_set())

    def test_each_phase_asks_its_own_question(self):
        for state, key in ((dict(_saving_sound=True), "room_stop_ask_sound"),
                           (dict(_rec_started=True, _fetching_full=True), "room_stop_ask_full")):
            app, asked = self.stop_with(False, **state)
            self.assertEqual(asked, [(key, "no")])

    def test_stop_before_anything_is_recorded_needs_no_question(self):
        app, asked = self.stop_with(False, _rec_started=False)
        self.assertEqual(asked, [])
        self.assertTrue(app._room_stop.is_set())

    def test_a_yes_after_the_recording_already_ended_changes_nothing(self):
        app = _RoomApp(self.dir)
        app._waiting_full, app._rec_started, app.t = False, True, lambda key, **kw: key
        old = vd.messagebox.askyesno
        vd.messagebox.askyesno = lambda *a, **k: setattr(app, "_room_active", False) or True
        try:
            app._stop_room()
        finally:
            vd.messagebox.askyesno = old
        self.assertFalse(app._room_stop.is_set())
        self.assertEqual(app.statuses, [])

    def test_closing_waits_for_the_killed_conversion_before_removing_its_file(self):
        order = []
        tmp = os.path.join(self.dir, "r.mp4.part")
        open(tmp, "w").close()
        proc = type("P", (), {"poll": lambda s: None, "kill": lambda s: order.append("kill"),
                              "wait": lambda s, timeout=None: order.append("wait")})()
        app = _RoomApp(self.dir)
        app._room_active = app._done_note = app._room_busy = app._running = app._scanning = False
        app._conv_proc, app._conv_tmp, app.destroy = proc, tmp, lambda: order.append("destroy")
        vd.App._close(app)
        self.assertEqual(order, ["kill", "wait", "destroy"])
        self.assertFalse(os.path.exists(tmp))

    def test_a_room_link_with_name_and_email_is_never_sent_unencrypted(self):
        room, q = vd.room_split_link("http://school.example/room/7/a?username=A&email=a@example.org")
        self.assertEqual(room, "https://school.example/room/7/a/")
        self.assertEqual(q["username"], "A")
        self.assertEqual(vd.room_split_link("http://127.0.0.1:8000/room/x")[0], "http://127.0.0.1:8000/room/x/")


if __name__ == "__main__":
    unittest.main(verbosity=1)
