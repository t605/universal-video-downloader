"""Offline tests of the course-page reading (GetCourse lesson lists).

    python tests\\test_scan.py

The HTML samples are made up in the shape of a real course page (no real titles, no tokens).
Development only - not part of the release zip.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import VideoDownloader as vd  # noqa: E402

BASE = "https://school.example"
ROW = """<tr><td class="item-image"></td><td class="item-main-td"><div class="vmiddle">
<div class="user-state-label is-stop-lesson"> Available (stop lesson) </div>
<div class="link title" href="/teach/control/lesson/view/id/%s"> %s
<span class="lesson-list__video-watched"> viewed </span> </div>
<div class="description"> A long description that must not end up in the name. </div></div></td></tr>"""


class LessonLinks(unittest.TestCase):
    def test_title_is_only_the_lesson_title(self):
        html = ROW % ("11", "First lesson") + ROW % ("12", "Second lesson")
        self.assertEqual(vd.gc_lesson_links(html, BASE), [
            (BASE + "/teach/control/lesson/view/id/11", "First lesson"),
            (BASE + "/teach/control/lesson/view/id/12", "Second lesson")])

    def test_duplicates_and_query_strings(self):
        html = (ROW % ("11", "One")) + '<a href="/teach/control/lesson/view/id/11?x=1">One again</a>'
        self.assertEqual(len(vd.gc_lesson_links(html, BASE)), 1)

    def test_plain_links_are_found_too(self):
        html = '<a href="/teach/control/lesson/view/id/5"> <b>Plain</b> link </a>'
        self.assertEqual(vd.gc_lesson_links(html, BASE), [(BASE + "/teach/control/lesson/view/id/5", "Plain link")])

    def test_page_order_is_kept(self):
        html = ROW % ("30", "C") + ROW % ("10", "A") + ROW % ("20", "B")
        self.assertEqual([t for _, t in vd.gc_lesson_links(html, BASE)], ["C", "A", "B"])

    def test_a_page_without_lessons(self):
        self.assertEqual(vd.gc_lesson_links("<html>nothing</html>", BASE), [])


class SubCourses(unittest.TestCase):
    def test_own_page_and_duplicates_are_left_out(self):
        html = ("<a href='/teach/control/stream/view/id/1'>me</a>"
                "<a href='/teach/control/stream/view/id/2'>a</a><a href='/teach/control/stream/view/id/2'>a</a>"
                "<a href='/teach/control/stream/view/id/3'>b</a>")
        self.assertEqual(vd.gc_substreams(html, BASE, BASE + "/teach/control/stream/view/id/1"),
                         [BASE + "/teach/control/stream/view/id/2", BASE + "/teach/control/stream/view/id/3"])


class CourseTitle(unittest.TestCase):
    def test_title_becomes_a_safe_folder_name(self):
        html = '<html><head><title>Course "Spring": part 1 &amp; 2 </title></head></html>'
        name = vd.gc_course_title(html)
        self.assertEqual(name, "Course Spring part 1 & 2")
        for bad in '\\/:*?"<>|':
            self.assertNotIn(bad, name)

    def test_no_title_gives_a_default(self):
        self.assertEqual(vd.gc_course_title("<html></html>"), "Course")
        self.assertEqual(vd.gc_course_title("<title>  </title>"), "Course")


if __name__ == "__main__":
    unittest.main(verbosity=1)
