# Universal Video Downloader 9.22 - fix: some course videos did not download

**The bug:** on some course pages the program found the video but stopped with "Requested format is not available". The cause:
the video had only one picture quality, slightly above the 480p limit (484p), with the sound in a separate stream, and the program
had no choice left. **Now** it takes the smallest quality above 480p when nothing at or below 480p exists, and still prefers 480p
whenever the video has it. Install this Setup over 9.21 (settings and downloads stay).

*Built with Claude Code: the rules and decisions are the owner's, the program code was written with Claude Code.*

## Files

| File | Size | SHA-256 |
|---|---|---|
| UniversalVideoDownloader-Setup.exe (recommended) | 51.5 MB | `AFDB83B531D1C191B655FAAC4392B9742114333C4C171AE8F3BFF73D474923E9` |
| UniversalVideoDownloader.zip (alternative: a `.bat` launcher) | 0.1 MB | see the file list of this release |

## Tested

- A real course page that failed before now downloads: 5 min 33 s, picture and sound, checked with FFmpeg.
- 4 new automated tests for the quality choice (only 484p; 480p preferred over larger; nothing at or below 480p; picture and sound in one stream),
  and the old choice rule was confirmed to fail on the same fake stream. 91 automated offline tests pass in total.
- **Not tested yet:** a clean second PC, Windows 10, screen scaling above 100 %, other webinar platforms. See the 9.21 notes for the full list.

Everything else is as in 9.21: Install steps, the manuals `README.txt` and `README_RU.txt`, the limits (no copy-protected video, no CAPTCHA login,
Windows 10/11 64-bit only) and the licence (MIT, third-party notices in `THIRD-PARTY-NOTICES.txt`).
