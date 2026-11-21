# Universal Video Downloader

A Windows program that saves videos from **webinars and online-course websites** to your own computer.
Paste a link, press one big green button. Made for people who are not technical: plain-language messages,
large high-contrast window, English and Russian.

> Built with Claude Code: the rules and decisions are the owner's, the program code was written with Claude Code.

## What it does

- **Course websites and private lessons.** Log in once with your own e-mail and password (for course sites built on
  GetCourse) or with an exported login file (any site), paste the address of a course page, press "Find videos":
  the program opens every lesson, lists all the videos, and saves the ones you tick into a folder named after the course.
- **Webinar rooms and school webinar pages.** Paste the link of a live webinar, press "Start recording" **before** it
  begins, and the program records the broadcast (480p, about 1 GB per hour) and saves it as an MP4: rooms whose video comes
  from Rutube or VK, and GetCourse school webinar pages (`/pl/webinar/show`, also with the name-and-e-mail entry). A VK room
  that is already on air gives only the last half minute; after the end the program waits (up to 4 hours) for VK's own
  full recording and saves that instead.
- **One video from a link** from Vimeo, VK, Kinescope players and about 1,700 other sites known to the download engine
  (not every one works), YouTube among them. Saves at 480p. Optional "Sound only (MP3)".
- **Convert to MP4** for recordings that are not in MP4 form.
- Messages in plain words: what went wrong and what to do next.

## Install (Windows 10 / 11)

1. Download `UniversalVideoDownloader-Setup.exe` from the **Releases** page of this repository.
2. Double-click it. Windows may show "Windows protected your PC" because the file is not signed with a paid
   certificate: click **More info**, then **Run anyway** (only if you downloaded it from this page).
3. Click Next, then Install. Nothing else needs to be installed: the download engine and FFmpeg are inside.
   It installs for your user only, with no administrator rights, and puts an icon on the desktop.

There is also a zip with a `.bat` launcher (it installs Python and the packages by itself on the first run).
The full step-by-step manual, written for beginners, is `README.txt` (English) and `README_RU.txt` (Russian), in the Setup and in the zip.

## What it cannot do

- Copy-protected (DRM) video, such as Netflix, many subscription theatre, film and sports sites. The program says so
  and does not try to get around the protection.
- Log in to sites that ask for a CAPTCHA or a code sent by text message with a password: use the exported login file.
- Windows only.
- Webinar platforms other than Bizon365 rooms (Rutube or VK video) and GetCourse webinar pages.

## Is it all right to download this?

For your **own private use**, with **your own login**, and only where the website's terms allow it. Many websites forbid
downloading, and recording a webinar can break its rules. You are responsible for what you save. The program does not bypass
copy protection. This is not legal advice. The software is provided "as is", without warranty. It is not connected to or
approved by YouTube, VK, Vimeo, GetCourse, Kinescope or any other website named here.

## What was tested, and what was not

Tested: the offline tests of the program (`python tests\test_room.py` and the other files in `tests`), real downloads of
course lessons and a public video on a Windows 11 PC, the course-page scan on one real course, three real live webinars of a
school (recorded, MP4 decoded without errors), and one real VK broadcast (recorded live; VK's full recording, 2 h 28 min, was
downloaded after the end with the program's own functions and its length matched). **Not tested:** the whole VK sequence
inside the program window, a clean second PC, Windows 10, screen scaling other than 100 %, other webinar platforms, every one
of the 1,700 sites.

## Build it yourself

Python 3.11+ and the packages `yt-dlp[default]`, `truststore`, `imageio-ffmpeg`: run `VideoDownloader.py`.
`build_release.ps1` builds the zip, `build_installer.ps1` builds the Setup (needs PyInstaller and Inno Setup 6).

## License

MIT, see `LICENSE`. The Setup also contains other free software with their own licenses (FFmpeg is GPLv3):
see `THIRD-PARTY-NOTICES.txt`.
