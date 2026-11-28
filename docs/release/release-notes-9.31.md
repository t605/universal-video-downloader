# Universal Video Downloader 9.31 - entry forms, name-only webinars, lost connections, safer buttons

**Fixed:**

- **Name-only entry.** A webinar page that says 'please introduce yourself' and asks only for a name is now supported (the e-mail field of the window may stay empty). The entry has worked on one real school. Recording such a webinar no longer answers 'log in first' after it (new in 9.31); a recording during a broadcast has not been tried yet.
- **Name-and-e-mail entry.** The program sent a school's form without the request signature of the school's page and without its consent boxes (offer, personal data), which is probably why a real school did not process it and the program showed the same message every time. Both are sent now; your tick in the program's window means that you agree to the school's boxes. No advertising mail is ever ticked. When the school answers with its own words, they are shown. When it accepts the form but you are still not logged in, the message says so and the button stays off. **Not yet confirmed on a real school.**
- **Lost connection.** While a finished recording is being saved, the program waits (up to 30 minutes) for a lost connection and goes on by itself, instead of leaving holes; after that it ends the recording and says it is not complete. A shortened piece is not accepted, and a missing first piece is an error.
- **A file whose name ends like ".f1"** is no longer deleted as an unfinished piece.
- **Closing during a conversion** no longer starts a second conversion pass.
- **"Stop and save"** asks first once video is being saved and says what would be lost; a recording stopped early says so.
- **No sleep** during ordinary downloads and during "Convert to MP4" (before: only during webinar recording).
- **Room links** that start with http are sent over https, because they hold a name and an e-mail.
- **Messages:** a full disk has its own plain message; after a language switch the hints under the link box are in the new language; the "no video found" message names logging in first.

**New since 9.28, the last published version** (9.29 and 9.30 were not published): a new look in the Windows 11 style with a menu on the left and one blue main button; recording of Kinescope webinar rooms with picture and sound; entry forms with a phone field; safer questions; private parts of addresses masked in the log.

**To upgrade:** close the program, then run the new Setup file (Windows may ask: "More info", then "Run anyway"; the file is not signed). Saved logins stay.

**Known limits:**

- A running broadcast cannot wait for a lost connection. A connection lost between the sound and the picture of a recording ends it after 3 minutes; sleep of the computer cuts the waiting short.
- The entry by name refuses a school page that forwards to a different web address (for safety).
- A piece the video server refuses is skipped (the message says the video is not complete).
- Entering a school by name or name and e-mail depends on the school: it may still ask for a password or a confirmation.
- Keyboard focus is hard to see on the blue buttons; Windows scaling of 125-150 % on a 1080p screen may hide the bottom of the window.

*Built with Claude Code: the rules and decisions are the owner's, the program code was written with Claude Code.*

## Files

| File | Size | SHA-256 |
|---|---|---|
| UniversalVideoDownloader-Setup.exe (recommended) | 51.6 MB | `0BCFDD87566BECA599615F4A91675A252BFBA7A77CEFA99EE0B9B94AE10175FC` |
| UniversalVideoDownloader.zip (alternative: a `.bat` launcher) | 0.1 MB | `DA61D6EA869DF97178F00700E74F2B78558CB45D6E93BFE18F5386C9FF12F632` |

## Tested

- 260 automated offline tests pass (108 room, 25 audio and file names, 22 login, 8 scan, 7 engine, 23 texts, 67 webinar pages).
- Every page of the window was measured in both languages at the default and the smallest size: nothing is clipped (measured with 9.30; the layout and the window texts have not changed since).
- Early use of 9.31 on a real PC: several different webinars started and work so far, as reported by the person using it. Five video files saved after 9.31 was installed (3 minutes to 1 h 57 min) have a picture and a sound track according to their headers; they were not decoded in full.
- With version 9.29 on a real PC: a whole Kinescope room recording (2 h 43 min), a 4 h 19 min webinar and a 1 h 52 min lesson, all with picture and sound, decoded without errors.
- **Not tested:** a recording during a broadcast after a name-only entry; the name-and-e-mail entry succeeding on a real school; a real internet break (made-up servers only); the new window on a screen with scaling above 100 %, on a clean PC, on Windows 10, with a screen reader, and by the people it is made for; a whole live webinar through the window.
