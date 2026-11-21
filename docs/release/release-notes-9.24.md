# Universal Video Downloader 9.24 - live school webinars can be recorded

**New:** the button "Record a webinar room" now records a **live broadcast** of a school's own webinar page (the web address contains
`/pl/webinar/show`). Paste the link, press "Start recording", keep the computer on. The program takes the live stream, saves every piece
in order and, when the broadcast ends, makes an MP4. A webinar that is a pre-recorded "auto-webinar" (a video played on a schedule) is
also supported: the program asks the school for the whole video and saves it from its first second.

**Start BEFORE the webinar.** A live broadcast gives only the last minute or two of picture at any moment, so the recording starts at the
moment you press the button (plus a little before). What was broadcast earlier is not available.

**If the school has no password** (you enter by pressing "Enter the room" and giving a name and e-mail): on the room page there is a new
button which fills in the school's own entry form for you (name, e-mail, a tick for consent). Then press "Start recording". You can also use
a login file exported from your browser (README, Option B). The program does not store your name or e-mail, only the school's cookies.

**Fixed:** the warning "the length of the video does not match" appeared after correct recordings, because the program trusted the length
that FFmpeg *guesses* for a `.ts` working file. Now the whole file is read to measure its real length. The MP4 is the file to keep; the
`.ts` is only a working copy and the program removes it after the MP4 is checked.

Version 9.24 also contains 9.22 and 9.23 (course videos whose best quality is just above 480p; reading of school webinar pages).
Install this Setup over the older one: settings, logins and downloads stay.

*Built with Claude Code: the rules and decisions are the owner's, the program code was written with Claude Code.*

## Files

| File | Size | SHA-256 |
|---|---|---|
| UniversalVideoDownloader-Setup.exe (recommended) | 51.5 MB | `1D5E2FBADDB4B9254CA3D544BC6673D28863CAA4CC0E9412D3F973F52E8AB008` |
| UniversalVideoDownloader.zip (alternative: a `.bat` launcher) | 0.1 MB | `27C3EF724E37284011F0B8E98B4C3613527A0452B28B393B04634507960756D1` |

## Tested

- 128 automated offline tests pass (34 room, 13 audio, 22 login, 8 scan, 7 engine, 7 further, 37 webinar pages and entry form).
- **Real live broadcast, 2026-11-17:** a school webinar was recorded through the program, 3 h 04 min 53 s, 8.2 GB. A separate full check of
  the MP4 (every frame decoded start to end): 0 decode errors, no timestamp gaps, picture and sound in step, no missing pieces, and the
  decoded picture and sound are identical to the `.ts` working file. Playing the picture and listening to the sound was not part of that
  check. The first hour of that webinar is missing because the recording was started late (see "Start BEFORE").
- The Setup installs (1194 files, exit code 0) and the program opens in 2-3 seconds.
- **Not tested:** the new "enter the room" button on a real school (only on a made-up school), the pre-recorded auto-webinar path end to
  end on the real school, a clean second PC, Windows 10, screen scaling above 100 %, how long a saved school login stays valid (the school
  decides; if the program says "no broadcast address" again, log in again). See the 9.21 notes.

Everything else is as in 9.21: install steps, `README.txt` / `README_RU.txt` (the Russian guide does not describe the new button yet),
limits (no copy-protected video, no CAPTCHA login, Windows 10/11 64-bit only), licence MIT with third-party notices.
