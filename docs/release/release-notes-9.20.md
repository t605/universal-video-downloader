# Universal Video Downloader 9.20 - first public release

A Windows program that saves videos from **webinars and online-course websites** to your own computer. Paste a link, press one big green button. Made for people who are not technical: plain-language messages, a large high-contrast window, English and Russian.

*Built with Claude Code: the rules and decisions are the owner's, the program code was written with Claude Code.*

## What you can do with it

- **Download a whole course.** Log in once (with your e-mail and password for course sites built on GetCourse, or with an exported login file for any site), paste the address of the course page and press "Find videos". The program opens every lesson, lists all the videos, and saves the ones you tick into a folder named after the course. Files are numbered with the lesson titles, so they stay in the order of the course.
- **Record a webinar.** Paste the link of a live webinar room: the program records the broadcast from its beginning and saves it as an MP4.
- **Save a single video** from Vimeo, VK, Kinescope players and many other sites (the download engine knows about 1,700 sites, but not every one works), YouTube among them. 480p quality. Optional "Sound only (MP3)" and "Convert to MP4".
- **Plain words.** Every message says what went wrong and what to do next.

## Install

1. Download **UniversalVideoDownloader-Setup.exe** below.
2. Double-click it. If Windows shows "Windows protected your PC", click **More info**, then **Run anyway**. (The file is not signed with a paid certificate, so Windows does not know it yet. Check the fingerprint below if you want to be sure it is the file from this page.)
3. Click Next, then Install. Nothing else needs to be installed: the download engine and FFmpeg are inside. It installs for your user only, needs no administrator rights, and puts an icon on the desktop.

The step-by-step manual for beginners is `README.txt` (it is also installed with the program).

## Files

| File | Size | SHA-256 |
|---|---|---|
| UniversalVideoDownloader-Setup.exe (recommended) | 51.5 MB | `3FDD775EB5DD09EEE260CD711C40E4011F8AB2CE8860AC4F90FD8A508D4526AA` |
| UniversalVideoDownloader.zip (alternative: a `.bat` launcher that installs Python and the packages by itself on the first run) | 0.1 MB | see the file list of this release |

## Safe by design

- Your password goes only to the website you log in to, only over https, and is never saved or written to the log.
- The saved login file stays on your computer. "Log out (delete saved logins)" removes it.
- The Setup updates its download engine by itself (about twice a day, from github.com, size-limited and checked against the published checksum). Nothing else about you is sent.

## What it cannot do

- Copy-protected (DRM) videos, such as Netflix and many subscription theatre, film and sports sites. The program says so and does not try to get around the protection.
- Log in with a password to sites that ask for a CAPTCHA or a text-message code. Use the exported login file instead.
- Windows only. Webinar recording is built for one room type (Rutube-based rooms); other webinar platforms are not supported yet.

## What was tested, and what was not

- **Tested:** 80 automated offline tests pass. A real course page of 13 lessons was scanned and its lessons downloaded; a public video was downloaded with the installed program; the Setup was installed, started and uninstalled on one Windows 11 PC; the engine update was tested against the real GitHub release.
- **Not tested yet:** a clean second PC, Windows 10, screen scaling above 100 %, the Windows SmartScreen screen on a new PC, other webinar platforms, and every one of the 1,700 sites.

## Is it all right to download this?

For your **own private use**, with **your own login**, and only where the website's terms allow it. Many websites forbid downloading, and recording a webinar can break its rules. You are responsible for what you save. This is not legal advice. The software is provided "as is", without warranty, and is not connected to or approved by YouTube, VK, Vimeo, GetCourse, Kinescope or any other website named here.

## License

MIT. The Setup also contains other free software under its own licenses; FFmpeg is a GPLv3 build. See `THIRD-PARTY-NOTICES.txt`.
