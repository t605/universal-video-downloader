# Universal Video Downloader 9.29 - a new look in the Windows 11 (Fluent 2) style

9.29 changes how the window looks and is operated; it does not change what the program downloads or records (9.28 is the version before it).

**What is new:**

- **A menu on the left.** The five pages (Download video, Several videos, Record a webinar, Log in to websites, Details for helper) are now in a menu on
  the left with an icon and a name each. The open page is marked by a bar, a white row and bold blue text, so it is not shown by colour alone.
  The links at the bottom and the "Back" buttons are gone. Tab reaches every menu row; Enter or Space opens it.
- **One blue main button.** The big button that does the work (Download video, Start recording, Download ticked videos, Log in) is now blue; green means
  only "done". All texts and guides that said "green button" now say "blue button".
- **Lighter header and a coloured status box.** The header is light with the owner's logo (on its own black tile, unchanged), the title, a green
  "All OK" pill and the language button. The message box at the bottom is tinted by kind (neutral, working, done, warning, error) and always has words and an
  icon, never colour alone.
- **Measured contrast.** Text on the page 15.9:1, grey help text 7.3:1, white text on the blue button 5.4:1, status texts 4.6:1 to 7.0:1, edges of boxes and buttons at least 3.3:1.
- **Webinar rooms that play a Kinescope video.** Bizon365 rooms (start.bizon365.ru and others) announce their video as a Kinescope recording; the program could not take that type before. It now reads the player with the room as Referer, takes the 480p stream and saves it whole, from its start, even if you press the button late. The player gives its pieces as byte ranges of one big file; the program now asks for exactly those bytes (a first try without that downloaded the whole file for every piece, 2.6 GB for two minutes). Tried on a real room: 45 seconds of work saved 25 minutes of video, 146 MB, decoded without errors. **Not tried:** the whole 2 h 43 min recording in one go, through the window.
- **A room link without a name and e-mail.** The button "The school asks for a name and e-mail?" now also works for such room links: it puts both into the link, and you press "Start recording".
- **A recorded webinar says so.** When a room plays a recording (not a live broadcast), the window now says "Saving the recorded webinar from its very start... saved so far: X of Y" instead of "Recording the broadcast", because it is saved faster than the webinar runs.
- **After the review.** Each page now says what to do on it in the message box (the calm message no longer begins with "Ready", which looked like a finished job); the title bar names the open page; a page that is not shown no longer takes Tab focus; every button, text box and list row has a visible focus frame; the disabled button is light, not a dark bar; the help of the webinar page is a short numbered list; the Tab order of the header follows the picture; the progress bar is a thin line.
- **A wider window.** It opens at 1120 x 840 (minimum 1000 x 840) because the menu needs room.
- **Not changed on purpose:** corners are square (the toolkit cannot round them without rewriting every button), there is no "Settings" page (the program has none), and the program
  does not follow the Windows high-contrast mode.

*Built with Claude Code: the rules and decisions are the owner's, the program code was written with Claude Code.*

## Files

| File | Size | SHA-256 |
|---|---|---|
| UniversalVideoDownloader-Setup.exe (recommended) | 51.6 MB | `AE0534FEA49B414AAA4D6531F0938BE0019FA5F9885E7A65A410A2C033A85283` |
| UniversalVideoDownloader.zip (alternative: a `.bat` launcher) | 0.1 MB | `D01897A8F73434C0565DEF3E90DFF99C572196DD9979807638D07E7EFD3ADEF0` |

## Tested

- 182 automated offline tests pass (69 room, 20 audio and file names, 22 login, 8 scan, 7 engine, 7 texts, 49 webinar pages).
- Every page of the window was measured in both languages at the default and the smallest size: nothing is clipped. The long status messages of the webinar recorder were measured too.
- **Not tested:** the new window on a screen with scaling above 100 %, on a clean PC, on Windows 10 (the icons fall back to Segoe MDL2 Assets there, or are left out), with a screen reader, and by the people it is made for.

Everything else is as in 9.28.
