# Universal Video Downloader 9.21 - clearer windows, safer, and a Russian guide

Version 9.21 is the update of the first public release (9.20). It fixes what a review of the finished program found when it was
tested like a first-time user: English and Russian, small windows, keyboard use, and the installer. **If you installed 9.20,
install this Setup over it** (the settings and your downloads stay).

*Built with Claude Code: the rules and decisions are the owner's, the program code was written with Claude Code.*

## What changed since 9.20

**Easier for beginners**
- **A Russian guide:** `README_RU.txt`, a short step-by-step manual in Russian, is installed with the program and is in the zip.
- **The Russian window fits at the smallest size.** Before, the status text, the last link at the bottom and the green button of the
  "Several videos on one page" screen were cut off. The smallest window is now larger, the status panel keeps a steady height, and
  button names no longer break across lines.
- **"Open folder" opens the course folder** after a course download (it used to open the whole Downloads folder).
- **After a login the program returns to the main page**, and the message now names buttons that are really on the screen.
- **The course page screen tells you where the videos will be saved**, and while it reads the lessons it shows "Reading lesson 7 of 13...".
- **Plainer words in Russian** (for example "Электронная почта или логин", the explanation of GetCourse and of the "I am not a robot" check),
  and correct singular forms in English ("1 video", not "1 videos").
- **One green button per screen:** on the login page "I exported it" is now blue.

**Keyboard**
- The links at the bottom of the window can be reached with the Tab key and opened with Enter or Space.
- Lessons in the list can be ticked with the Space bar (the active row is highlighted).

**Safer and tidier**
- Temporary copies of VK login cookies are now deleted when the program closes (before, they stayed in the temp folder).
- The engine update no longer retries at every start when the internet or GitHub is not reachable (at most every 12 hours).
- Before recording a webinar the program asks if the disk has less than 10 GB free (a 2-hour webinar needs about 8 GB).

**Installer**
- Installing over an older version removes the old program files first (no leftovers).
- The Setup now refuses to start on Windows older than 10, writes an install log, shows a version and publisher in the file properties,
  and installs the MIT licence and the third-party notices with the program.
- The README no longer advises to answer "Yes" to a Windows administrator question (the Setup never needs one), and explains the Windows 11
  "Smart App Control" case, where an unsigned program can be blocked with no "Run anyway" button.

## Install

1. Download **UniversalVideoDownloader-Setup.exe** below.
2. Double-click it. If Windows shows "Windows protected your PC", click **More info**, then **Run anyway**. (The file is not signed with a paid
   certificate, so Windows does not know it yet. Check the fingerprint below if you want to be sure it is the file from this page.)
3. Click Next, then Install. Nothing else needs to be installed: the download engine and FFmpeg are inside. It installs for your user only,
   needs no administrator rights, and puts an icon on the desktop.

The manuals are `README.txt` (English) and `README_RU.txt` (Russian); both are installed with the program.

## Files

| File | Size | SHA-256 |
|---|---|---|
| UniversalVideoDownloader-Setup.exe (recommended) | 51.5 MB | `9F9E1D5EB17770D5210C09C4DEE661886ADB7112102BFA0C3E12CDA7ED9F18B7` |
| UniversalVideoDownloader.zip (alternative: a `.bat` launcher that installs Python and the packages by itself on the first run) | 0.1 MB | see the file list of this release |

## What it cannot do

- Copy-protected (DRM) videos, such as Netflix and many subscription theatre, film and sports sites. The program says so and does not try to get around the protection.
- Log in with a password to sites that ask for a CAPTCHA or a text-message code. Use the exported login file instead.
- Windows only (Windows 10 or 11, 64-bit). Webinar recording is built for one room type (Rutube-based rooms).
- The program itself does not update by itself: only its download engine does. For a fix you install a new Setup over the old one.

## What was tested, and what was not

- **Tested:** 87 automated offline tests pass. The layout was checked from pictures of the program's own window (both languages, all pages,
  default and smallest size). A real course page of 13 lessons was scanned and a lesson downloaded; the Setup was installed, started and
  removed on one Windows 11 PC; the engine update was tested against the real GitHub release. The release was also reviewed by a batch of AI review agents
  (security, design, accessibility, internationalization, installer, performance, first-use walkthrough); what they found is fixed in this version.
- **Not tested yet:** a clean second PC, Windows 10, screen scaling above 100 %, the Windows SmartScreen and Smart App Control screens on a new PC,
  a real screen reader, other webinar platforms, and every one of the 1,700 sites.

## Is it all right to download this?

For your **own private use**, with **your own login**, and only where the website's terms allow it. Many websites forbid downloading, and recording a
webinar can break its rules. You are responsible for what you save. This is not legal advice. The software is provided "as is", without warranty, and
is not connected to or approved by YouTube, VK, Vimeo, GetCourse, Kinescope or any other website named here.

## License

MIT. The Setup also contains other free software under its own licenses; FFmpeg is a GPLv3 build. See `THIRD-PARTY-NOTICES.txt`.
