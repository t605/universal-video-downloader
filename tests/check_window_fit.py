"""Window-fit check (needs a screen; NOT part of the build tests): does every page fit inside the window?

Run it after ANY change to the layout or to a text, and before a release:
    python tests\\check_window_fit.py
For both languages and for the default AND the minimum window size it shows each page and compares the height the
page needs with the height the window gives it. Exit code 0 = nothing is clipped, 1 = at least one page is clipped.
It starts the real window briefly, uses a scratch data folder and never touches the network or the clipboard.
(Added 2026-11-20 after a button on the Russian room page was cut off at the old default size.)
"""
import os
import runpy
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPARE_MIN = 8   # pixels of free space we want to keep, so another font rendering cannot clip a page

sys.argv = ["x"]
os.environ["LOCALAPPDATA"] = os.path.join(tempfile.gettempdir(), "uvd_fit_check")
os.makedirs(os.environ["LOCALAPPDATA"], exist_ok=True)
mod = runpy.run_path(os.path.join(os.path.dirname(HERE), "VideoDownloader.py"), run_name="fitcheck")
mod["COOKIE_DIRS"][:] = []
app = mod["App"]()
app._read_clip = lambda: ""
app.update()
bad = 0
default_geo = f"{app.winfo_width()}x{app.winfo_height()}"
print(f"default window {default_geo}, minimum {app.minsize()[0]}x{app.minsize()[1]}")
for size in ("default", "min"):
    for lang in ("en", "ru"):
        if app._lang != lang:
            app._switch_lang()
            app.update()
            app._read_clip = lambda: ""
        if size == "default":
            app.geometry(default_geo)
        else:
            mw, mh = app.minsize()
            app.geometry(f"{mw}x{mh}")
        app.update()
        for page in ("main", "scan", "room", "cookies", "details"):
            app._show(page)
            app.update()
            app.update_idletasks()
            p = app._pages[page]
            spare = app._body.winfo_height() - p.winfo_reqheight()
            lowest = max(c.winfo_y() + c.winfo_height() for c in p.winfo_children())
            ok = spare >= SPARE_MIN and lowest <= app._body.winfo_height()
            if not ok:
                bad += 1
            print(f"{size:7} {lang} {page:8} {app.winfo_width()}x{app.winfo_height()}  spare {spare:4} px  {'ok' if ok else 'CLIPPED'}")
# The longest status messages of the room recorder must not push the page out of its space (added 2026-11-20).
STATUS_KEYS = [("busy", "st_room_wait_full", dict(h=4, w="3:59:59", r="3:59:59")), ("busy", "st_room_getting_full", dict(t="2:28:34")),
               ("busy", "st_room_checking", {}), ("busy", "st_room_rec_vod", dict(t="2:28:34", total="2:43:39")), ("busy", "st_room_rec_late", dict(t="2:28:34")),
               ("warn", "st_room_done_late", dict(t="2:28:34")), ("warn", "st_room_done_late_nofull", dict(t="2:28:34")),
               ("warn", "st_room_done_skipped", dict(n=12)), ("warn", "st_room_done_check", dict(t="2:28:34")),
               ("err", "room_err_gc_nostream", {}), ("err", "room_err_enc", {}),
               ("warn", "st_room_done_late_gaps", dict(t="2:28:34")), ("warn", "st_room_done_noaudio", {}),
               ("err", "room_err_audio", {}), ("err", "room_err_sound", {}), ("busy", "st_room_rec_sound", {}), ("warn", "st_done_part", dict(ok=11, n=13)), ("warn", "d_no_player", {}), ("warn", "st_room_net_wait", {}), ("err", "d_disk", {}), ("warn", "st_room_done_cut", dict(t="2:28:34", total="2:43:39")), ("warn", "st_room_done_stopped", dict(t="2:28:34"))]
for lang in ("ru", "en"):
    if app._lang != lang:
        app._switch_lang()
        app.update()
        app._read_clip = lambda: ""
    mw, mh = app.minsize()
    app.geometry(f"{mw}x{mh}")
    app._show("room")
    for kind, key, kw in STATUS_KEYS:
        app._set_status(kind, key, action="convfolder", **kw)
        app.update()
        app.update_idletasks()
        p = app._pages["room"]
        spare = app._body.winfo_height() - p.winfo_reqheight()
        ok = spare >= SPARE_MIN
        if not ok:
            bad += 1
        print(f"status  {lang} {key:26} {app.winfo_width()}x{app.winfo_height()}  spare {spare:4} px  {'ok' if ok else 'CLIPPED'}")
app.destroy()
print("pages clipped:", bad)
sys.exit(1 if bad else 0)
