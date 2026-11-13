"""Offline tests of the school sign-in (GetCourse login with e-mail + password).

    python tests\test_login.py

A fake school runs on this PC (plain http, 127.0.0.1) and behaves like the real login
page seen on 2026-11-13: GET /cms/system/login holds window.csrfToken / requestTime /
requestSimpleSign and the form id; POST gives JSON ("redirectUrl" or "errorMessage");
the lesson page redirects to the login page until the session cookie is present.
Test values only - never a real password. The real school was NOT contacted with a
login (see CLAUDE.md: not tested against a real account).

Development only - not part of the release zip.
"""
import html as htmllib
import json
import os
import re
import sys
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import VideoDownloader as vd  # noqa: E402

GOOD = ("pupil@example.test", "test-password-123")
LOGIN_PAGE = """<html><head><title>Login</title></head><body><form class="xdget-loginUserForm"></form>
<script>window.csrfToken = "CSRF123=="; window.requestTime = 1794570287;
window.requestSimpleSign = "abc123"; window.gcsObjectType = "cms_page"; window.gcsObjectId = "-1";
var tpl = {"xdgetId":99945,"type":"loginUserForm"};   /* editor template: NOT this page's form */
window.disableCaptchaForConfirmPhone = false;           /* every GetCourse page says "captcha" */
$(function(){ $('[data-xdget-id="r6288_1_1_1_1_1"]').xdget_userForm({ xdgetId: "r6288_1_1_1_1_1", type: "loginUserForm", params: {} }); });
</script></body></html>"""
FORM_ID = "r6288_1_1_1_1_1"


class School(BaseHTTPRequestHandler):
    mode = "ok"          # ok | captcha | nolesson | notgc
    seen = []

    def log_message(self, *a): pass

    def _send(self, code, body, ctype="text/html; charset=utf-8", extra=()):
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        for k, v in extra: self.send_header(k, v)
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/cms/system/login"):
            if School.mode == "nologin":
                return self._send(404, "not found")           # e.g. a YouTube address
            if School.mode == "notgc":
                return self._send(200, "<html>just a page</html>")
            return self._send(200, LOGIN_PAGE, extra=[("Set-Cookie", "PHPSESSID5=guest1; Path=/")])
        if self.path.startswith("/teach/control/lesson/view/id/1"):
            signed = "session=OK" in (self.headers.get("Cookie") or "")
            if signed and School.mode == "lesson404":
                return self._send(404, "gone")
            if signed and School.mode != "nolesson":
                return self._send(200, "<html>lesson with video</html>")
            self.send_response(302); self.send_header("Location", "/cms/system/login")
            self.send_header("Content-Length", "0"); self.end_headers(); return
        self._send(404, "no")

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        f = {k: v[0] for k, v in urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8")).items()}
        School.seen.append(f)
        if f.get("xdgetId") != FORM_ID:     # like the real site: a wrong form id gets the login PAGE back
            return self._send(200, LOGIN_PAGE)
        ok = (f.get("action") == "processXdget" and f.get("xdgetId") == FORM_ID
              and f.get("params[action]") == "login" and f.get("_csrf") == "CSRF123=="
              and f.get("requestTime") == "1794570287" and f.get("requestSimpleSign") == "abc123"
              and self.headers.get("X-Requested-With") == "XMLHttpRequest")
        if not ok:
            return self._send(400, "{}", "application/json")
        if School.mode == "echo":           # a page that repeats the password, HTML-escaped
            return self._send(200, LOGIN_PAGE + "<p>" + htmllib.escape(f.get("params[password]", "")) + "</p>")
        if School.mode == "pageanswer":
            return self._send(200, LOGIN_PAGE + "<p>" + GOOD[1] + "</p>")
        if School.mode == "redirect":
            self.send_response(307); self.send_header("Location", self.path)
            self.send_header("Content-Length", "0"); self.end_headers(); return
        if School.mode == "captcha":
            return self._send(200, json.dumps({"errorMessage": "Please solve the captcha"}),
                              "application/json")
        if (f.get("params[email]"), f.get("params[password]")) != GOOD:
            return self._send(200, json.dumps({"errorMessage": "<b>Wrong</b> password"}),
                              "application/json")
        self._send(200, json.dumps({"redirectUrl": "/"}), "application/json",
                   extra=[("Set-Cookie", "session=OK; Path=/")])


class SchoolLogin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), School)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        cls.tmp = tempfile.mkdtemp(prefix="vd_login_test_")
        cls._old = vd.LOGIN_DIR
        vd.LOGIN_DIR = cls.tmp

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); vd.LOGIN_DIR = cls._old

    def setUp(self):
        School.mode = "ok"; School.seen.clear()
        self.page = self.base + "/teach/control/lesson/view/id/1"

    def login(self, *a, **k):
        return vd.school_login(self.page, *a, allow_http=True, **k)   # plain http: test server only

    def err(self, *a):
        with self.assertRaises(vd.LoginError) as c:
            self.login(*a)
        return c.exception

    def test_https_is_required_for_real_use(self):
        with self.assertRaises(vd.LoginError) as c:
            vd.school_login(self.page, *GOOD)             # http:// without the test switch
        self.assertEqual(c.exception.args[0], "login_err_https")
        self.assertEqual(School.seen, [])                 # nothing was sent

    def test_uses_the_pages_own_form_id_not_the_template_number(self):
        self.login(*GOOD)
        self.assertEqual(School.seen[0]["xdgetId"], FORM_ID)

    def test_a_page_as_answer_is_not_reported_as_captcha(self):
        School.mode = "pageanswer"          # answer is HTML that merely contains the word "captcha"
        e = self.err(*GOOD)
        self.assertEqual(e.args[0], "login_err_other")
        self.assertIn("not JSON", e.info)
        self.assertNotIn(GOOD[1], e.info)   # the password never shows in the detail text

    def test_user_at_host_address_is_refused_before_anything_is_sent(self):
        for bad in ("https://school.example@evil.example/teach/x", "https://school.example\\@evil.example/x",
                    "https://evil example/x"):
            with self.assertRaises(vd.LoginError) as c:
                vd.school_login(bad, *GOOD)
            self.assertEqual(c.exception.args[0], "login_err_address", bad)
        self.assertEqual(School.seen, [])

    def test_escaped_password_in_an_answer_page_is_masked(self):
        School.mode = "echo"
        e = self.err("a@b.test", "p&ss<w>rd")
        self.assertNotIn("p&amp;ss&lt;w&gt;rd", e.info)
        self.assertNotIn("p&ss<w>rd", e.info)

    def test_login_page_404_means_not_a_getcourse_site(self):
        School.mode = "nologin"
        self.assertEqual(self.err(*GOOD).args[0], "login_err_site")   # not "ask your helper"

    def test_unreadable_lesson_page_keeps_the_login(self):
        School.mode = "lesson404"
        path, checked = self.login(*GOOD)
        self.assertTrue(os.path.isfile(path))
        self.assertFalse(checked)                         # saved, but "could not check"

    def test_checked_flag_is_true_when_the_lesson_opens(self):
        self.assertTrue(self.login(*GOOD)[1])

    def test_post_is_never_redirected_with_the_password(self):
        School.mode = "redirect"
        e = self.err(*GOOD)
        self.assertEqual(e.args[0], "login_err_other")
        self.assertEqual(len(School.seen), 1)             # the password went out once, not again

    def test_cookie_file_for_prefers_the_file_that_covers_the_host(self):
        from types import SimpleNamespace
        a = os.path.join(self.tmp, "a.txt"); b = os.path.join(self.tmp, "b.txt")
        row = "\t".join(["{}", "FALSE", "/", "FALSE", "9999999999", "n", "v"]) + "\n"
        open(a, "w").write("# Netscape HTTP Cookie File\n" + row.format("other.example"))
        open(b, "w").write("# Netscape HTTP Cookie File\n" + row.format("school.example"))
        app = SimpleNamespace(_cookies_file=a, _cookie_files=[(a, 0, []), (b, 0, [])], _auto_cookie=a)
        self.assertEqual(vd.App._cookie_file_for(app, "https://school.example/x"), b)
        self.assertEqual(vd.App._cookie_file_for(app, "https://elsewhere.example/x"), a)

    def test_success_writes_a_usable_cookie_file(self):
        path, _ = self.login(*GOOD)
        self.assertTrue(path.startswith(self.tmp) and os.path.isfile(path))
        self.assertFalse(os.path.exists(path + ".tmp"))   # written whole, then renamed
        self.assertTrue(vd.valid_cookiefile(path))
        header = vd.cookie_header_for(path, "http://127.0.0.1/lesson")   # (host_of keeps a :port)
        self.assertIn("session=OK", header)
        # the saved file must not hold the password or the e-mail
        raw = open(path, encoding="utf-8").read()
        self.assertNotIn(GOOD[1], raw); self.assertNotIn(GOOD[0], raw)

    def test_sends_what_the_real_form_sends(self):
        self.login(*GOOD)
        f = School.seen[0]
        self.assertEqual(f["params[url]"], self.base + "/cms/system/login")
        self.assertEqual(f["params[object_type]"], "cms_page")
        self.assertEqual(f["params[object_id]"], "-1")

    def test_wrong_password(self):
        e = self.err(GOOD[0], "nope")
        self.assertEqual(e.args[0], "login_err_bad")
        self.assertIn("Wrong password", e.info)             # html tags removed

    def test_captcha_is_reported_not_bypassed(self):
        School.mode = "captcha"
        self.assertEqual(self.err(*GOOD).args[0], "login_err_captcha")

    def test_not_a_getcourse_site(self):
        School.mode = "notgc"
        self.assertEqual(self.err(*GOOD).args[0], "login_err_site")

    def test_login_accepted_but_lesson_still_locked(self):
        School.mode = "nolesson"
        self.assertEqual(self.err(*GOOD).args[0], "login_err_verify")

    def test_no_website_reachable(self):
        with self.assertRaises(vd.LoginError) as c:
            vd.school_login("http://127.0.0.1:9/teach/x/1", *GOOD, timeout=3, allow_http=True)
        self.assertEqual(c.exception.args[0], "login_err_net")

    def test_not_a_link(self):
        with self.assertRaises(vd.LoginError):
            vd.school_login("hello", *GOOD)

    def test_disk_error_has_its_own_message(self):
        old = vd.LOGIN_DIR
        vd.LOGIN_DIR = os.path.join(self.tmp, "a.txt", "sub")   # a file in the way: cannot be a folder
        try:
            open(os.path.join(self.tmp, "a.txt"), "w").close()
            self.assertEqual(self.err(*GOOD).args[0], "login_err_disk")
        finally:
            vd.LOGIN_DIR = old


class Texts(unittest.TestCase):
    KEYS = ["login_btn", "login_help", "login_title", "login_site", "login_email", "login_pass",
            "login_show", "login_go", "login_cancel", "login_busy", "login_ok", "login_ok_unchecked",
            "login_err_empty", "login_err_https", "login_err_site", "login_err_bad",
            "login_err_captcha", "login_err_verify", "login_err_net", "login_err_disk",
            "login_err_other", "login_err_address", "login_site_said", "act_login", "logout_btn", "logout_q",
            "logout_none", "logout_done", "clip_paste", "clip_copy", "clip_cut"]

    def test_both_languages_have_every_text(self):
        for k in self.KEYS:
            for lang in ("en", "ru"):
                self.assertIn(k, vd.T[lang], f"{k} missing in {lang}")

    def test_every_error_key_the_code_can_raise_has_a_text(self):
        src = open(vd.__file__, encoding="utf-8").read()
        for k in set(re.findall(r'LoginError\("(login_err_\w+)"', src)):
            self.assertIn(k, vd.T["en"]); self.assertIn(k, vd.T["ru"])

    def test_login_dir_is_searched_for_cookie_files(self):
        self.assertIn(vd.LOGIN_DIR, vd.COOKIE_DIRS)


if __name__ == "__main__":
    unittest.main(verbosity=1)
