===============================================================
  UNIVERSAL VIDEO DOWNLOADER                       version 9.20
  Saves videos from the internet to your computer, in 480p
===============================================================

It can record a live webinar and save it as an MP4 file. It
saves lessons from online course websites, including private
lessons you log in to. It finds several videos on one page. It
works with Vimeo, VK and many other websites (the download
engine knows about 1,700 of them, but not every one works),
including YouTube.

Built with Claude Code: the rules and decisions are the
owner's, the program code was written with Claude Code.

The program speaks English or Russian - see "Language" in
section 6.

Afraid of getting something wrong? You cannot break your
computer with this program. Read ONE step. Do that step. Then
read the next one. Take your time.


CONTENTS
--------
  1. What this program is, and what you need
  2. Installing with the Setup file
  3. Your first download
  4. Several videos on one page
  5. Log in to websites (a mini-guide you can read alone)
     Option A: with a password   Option B: a login file
  6. Other features
     Webinar rooms, Sound only (MP3), Convert to MP4, course
     pages, VK live broadcasts, language
  7. If something goes wrong
  8. Is it all right to download this?
  9. What it cannot do
 10. Files and folders
     Quick reference
     Words explained
     Appendix: the older way to install (zip file)


---------------------------------------------------------------
  1. WHAT THIS PROGRAM IS, AND WHAT YOU NEED
---------------------------------------------------------------

Universal Video Downloader saves a video from a web page onto
your computer. Then you can watch it later, without the
internet.

How it works, in three moves:
  1. You copy the address of the video page.
  2. You press one big green button.
  3. The video appears in a folder on your computer.

WHAT YOU NEED
  * A Windows 10 or 11 computer.
  * An internet connection.
  * About 300 MB of free disk space for the program, plus room
    for your videos.
  * The Setup file  UniversalVideoDownloader-Setup.exe . You
    got it from the person who made this program for you.

You do NOT need to install anything else. Everything the
program needs is already inside the Setup file.

GOOD TO KNOW
  * It costs nothing.
  * Videos are saved in 480p on purpose. That is clear enough
    for a laptop or tablet, and the files stay small.
  * The program looks at what you copied only when you switch
    to its window, and only if it is a web address. It never
    downloads anything until you press the green button.


---------------------------------------------------------------
  2. INSTALLING WITH THE SETUP FILE  (about 5 minutes, once)
---------------------------------------------------------------

You do this once. Afterwards you start the program like any
other program.

STEP 1 - Put the Setup file where you can find it
-------------------------------------------------
WHAT: Save or copy  UniversalVideoDownloader-Setup.exe  to the
Desktop or to the Downloads folder.
YOU WILL SEE: the file with its name. It is a big file (about
52 MB), so copying can take from a few seconds to a minute.
Wait for it.

STEP 2 - Open it
----------------
WHAT: Double-click the Setup file. Click twice, fast, with the
left mouse button.
YOU WILL SEE: maybe a small window "Select Setup Language".
Choose English or Russian and press "OK".
IF NOTHING HAPPENS: wait a few seconds. Then try once more.

STEP 3 - If Windows shows a blue box
------------------------------------
YOU MAY SEE: a blue box with the words

    "Windows protected your PC"

Do not be afraid. Windows shows this box for every small
private program. It does not come from a big company. The box
does not mean the file is dangerous.

Do this ONLY if the file came from the person who made the
program for you:

  1. Click the words "More info". They are a small link in
     the box.
  2. A new button "Run anyway" appears. Click it.

YOU WILL SEE: the Setup window opens.
If the file came from somebody else, or you are not sure:
close the box and ask the person who made the program.

Windows may also ask "Do you want to allow this app to make
changes to your device?". The Setup needs no administrator
rights, so you normally will not see this question. If you do
see it, and the file came from the person who made the program
for you, click "Yes". If you are unsure, stop and ask your
helper.

STEP 4 - Go through the Setup window
------------------------------------
The Setup window has a few pages. On every page you press a
button at the bottom right. You will see these pages, one
after the other:

  1. "Welcome to the Universal Video Downloader Setup Wizard"
     -> press "Next".
  2. "Select Additional Tasks". There is a tick box
     "Create a desktop shortcut". Leave it ticked. You get a
     picture of a white panda on your Desktop.
     -> press "Next".
  3. "Ready to Install" -> press "Install".
  4. "Installing". A bar fills up. Wait. This takes from a few
     seconds to a minute or two. Do not close the window.
  5. The last page has a tick box "Launch Universal Video
     Downloader". Leave it ticked. -> press "Finish".

The Setup does not ask where to put the program. It installs it
for your Windows user only, into this folder:

    %LOCALAPPDATA%\Programs\Universal Video Downloader

You never need to open that folder. The Setup also adds
"Universal Video Downloader" to the Start menu, and "Universal
Video Downloader - Read me", which opens this file.

STEP 5 - The program opens
--------------------------
YOU WILL SEE: the Universal Video Downloader window.
If it does not open, start it as described just below.
The installation is done. You can delete the Setup file or
keep it. You need it again only to install again.

HOW TO START THE PROGRAM LATER
  * Double-click the white panda picture "Universal Video
    Downloader" on the Desktop, or
  * Press the Windows key on your keyboard, type  Universal
    (or  Video ) and press Enter.

IF AN ANTIVIRUS PROGRAM COMPLAINS
A brand new program can trigger a false alarm in some
antivirus programs. Do not switch the antivirus off. Stop, and
ask the person who made the program for you.

HOW TO UNINSTALL
  1. Press the Windows key, type  Settings , press Enter.
  2. Click "Apps", then "Installed apps".
  3. Find "Universal Video Downloader". Click the three dots
     next to it.
  4. Click "Uninstall" and answer the questions.
This also deletes the logins the program saved (section 5) and
the engine update. The videos you downloaded are NOT deleted.

If you also used the zip version (see the appendix), it shares
the same data folder, %LOCALAPPDATA%\VideoDownloader.
Uninstalling the Setup then also deletes the saved logins of
the zip version.

KEEPING THE PROGRAM UP TO DATE
Websites change often. So the part of the program that gets
videos (the "download engine") must be refreshed now and then.
The program does it by itself. When you are online, it contacts
github.com, at most twice a day, and fetches the newest engine
from the official yt-dlp release. Nothing else about you is
sent. The new engine is used the next time the program starts.

If a website stops working, see "A website stopped working" in
section 7.


---------------------------------------------------------------
  3. YOUR FIRST DOWNLOAD
---------------------------------------------------------------

The main window has one big green button, "Download video".

STEP 1 - Open the page with the video
  WHAT: In your web browser (Chrome, Edge), open the page.
  YOU WILL SEE: the video, or the lesson with the video.

STEP 2 - Copy the address
  WHAT: Look at the bar at the very top of the browser. It
  shows the web address. Click once inside that bar. The text
  becomes blue. Press the CTRL key and the C key together.
  YOU WILL SEE: nothing. That is fine. The address is copied.

STEP 3 - Switch to Universal Video Downloader
  WHAT: Click the Universal Video Downloader picture in the bar
  at the bottom of the screen.
  YOU WILL SEE: the address is already in the box. If the box
  is empty, press the blue button "Paste link".

STEP 4 - Check that it is the right video
  YOU WILL SEE: under the box a line like
     Found: Introduction to painting
            vimeo.com  .  12:30
  That is the title, the website and the length. Then the box
  at the bottom says: "The link is fine. Press the green
  button "Download video"."
  IF YOU SEE something else: see section 7, "The link".

STEP 5 - Press the green button
  WHAT: Click the big green button "Download video".
  YOU WILL SEE: the box at the bottom shows "Downloading..."
  and a number that grows to 100%, and about how many minutes
  are left. Wait. Do not close the window.

STEP 6 - Done
  YOU WILL SEE: "Done! The video is saved." and a blue button
  "Open folder" next to it.
  WHAT: Click "Open folder". A window opens with your video.

WHERE THE VIDEOS GO
-------------------
The line "Videos are saved in:" shows the folder. At first it
is your Downloads folder. "Open folder" opens it. "Change"
lets you pick another folder. The program remembers your
choice.

If you press a button before you copied an address, the
program says: "First copy a video's address in your browser,
then press "Paste link"." Do exactly that.


---------------------------------------------------------------
  4. SEVERAL VIDEOS ON ONE PAGE
---------------------------------------------------------------

Online courses often put many videos behind one page. This
collects them all at once, and downloads the ones you choose.

THE WHOLE COURSE IN SEVEN STEPS (for a course on a school's
website that needs your login)

  STEP 1 - LOG IN (only the first time).
     Do the steps of OPTION A in section 5 ("Log in with a
     password"). When the program says "Logged in to ...", you
     are done. The login stays saved: next time skip this step.

  STEP 2 - COPY THE ADDRESS OF THE COURSE PAGE.
     In your normal browser (Chrome, Edge), open the page of
     the course that LISTS ALL the lessons, one under the
     other. Click once in the address bar at the top, press
     Ctrl and C together. This is the address of the whole
     course, not of one lesson.

  STEP 3 - OPEN THE RIGHT SCREEN.
     In the program, look at the bottom of the window.
     Click the blue link "Several videos on one page".

  STEP 4 - PASTE THE ADDRESS.
     Press the blue button "Paste link".
     YOU WILL SEE: the address appears in the white box.

  STEP 5 - FIND THE VIDEOS.
     Press the blue button "Find videos".
     YOU WILL SEE: the button says "Looking..." Wait. The
     program opens every lesson, one after the other. A course
     of 13 lessons takes about 15 seconds. A course of 80
     lessons takes more than a minute. Do not press anything.
     YOU WILL SEE AT THE END: a list, one line per video, every
     line with a tick, and the message "Found 13 videos" (the
     number is the number of videos in your course).
     IF YOU SEE "No videos found": you are not logged in, or
     this is not the page that lists the lessons. Go back to
     step 1, or copy the address again (step 2).
     A course page is read for up to 150 lessons. If your
     course has more, the rest is not read. The program log
     (under "Details for helper") shows how many lesson pages
     it read.

  STEP 6 - CHOOSE.
     Every video has a tick. To skip a video, click its line:
     the tick goes away. "Untick all" removes all ticks, "Tick
     all" puts them all back.

  STEP 7 - DOWNLOAD.
     Press the big green button "Download ticked videos".
     YOU WILL SEE: a line like "Video 2 of 13:  45%" and a bar
     that fills up. Wait. At the end you see "Done! 13 of 13
     videos saved."
     The videos are in a NEW FOLDER inside your Downloads
     folder (or inside the folder shown on the main screen).
     The folder is named with the title of the course, as the
     course page gives it.
     Inside, each file is named with the number and the title
     of the lesson, for example "05 Lesson title.mp4", so they
     stay in the order of the course. If the course has parts
     (sub-courses), each part gets its own folder inside the
     course folder.
     Then press "Open folder". It opens the Downloads folder:
     open the course folder in it.

If one video fails, the program goes on with the next ones and
tells you at the end how many were saved.

THE SAME WORKS FOR ANY PAGE with several videos on it (a
lesson with five videos, a page of a webinar archive): copy
that page's address and follow steps 3 to 7.

Note: use the address of a REAL page. A specific course page
or lesson is good. The front page of a website is not. If
you use a front page, the program says: "This is the
website's front page. Open the lesson or channel you want
and copy that address."

A LIST OF LINKS IN A FILE
-------------------------
Instead of scanning a page, you can press "Open list file..."
and pick a file with video links:

  .txt   one link per line. Text before a link on the same line
         becomes the video's name, for example
            Week 1 - Introduction: https://.../lecture1.mp4
         The name may also be on the line above the link - the
         files saved by Coursera Link Collector work as they
         are.
  .json  a list of links, or of entries with "url" and "title"

The videos appear in the list, ticked. With names from the file
they are saved in order as "01 - Week 1 - Introduction.mp4",
"02 - ...". The number is the video's place in the file, so
unticking one does not change the others. A name that already
starts with a number (like "03 Installing ...") keeps it as is.
Download links from course websites often stop working after a
few hours - download them on the same day.


---------------------------------------------------------------
  5. LOG IN TO WEBSITES  (a mini-guide you can read alone)
---------------------------------------------------------------

WHEN DO YOU NEED THIS?
  * The video is on a website where YOU have an account. For
    example a course you paid for, or a membership.
  * You press the green button, and the program says it cannot
    find the video, or that the video is private.
  * Then the program must show that it is you. That is a login.

If a video downloads fine, you do not need this section.

+-------------------------------------------------------------+
|  BEFORE YOU START - check these four things                 |
|                                                             |
|  [ ] You know your e-mail (or username) for that website.   |
|  [ ] You know your password. You can see it on your own     |
|      screen or paper.                                       |
|  [ ] In your normal browser (Chrome or Edge) you can open   |
|      the same lesson, and you are logged in there.          |
|  [ ] The lesson plays in the browser.                       |
|                                                             |
|  If you cannot open the lesson in the browser yourself,     |
|  STOP. Ask the support of that website. The program cannot  |
|  open what your account cannot open.                        |
+-------------------------------------------------------------+

There are two ways to log in:

  OPTION A - with a password. Fast. It works only for course
             websites made with a system called GetCourse. You
             can tell by the web address of the lesson: it has
             /teach/ in it.
  OPTION B - with a "login file". It works for any website. It
             has more steps.

Try option A first if the address has /teach/ in it. In all
other cases, or if A does not work, use option B.


OPTION A - LOG IN WITH A PASSWORD
---------------------------------

STEP 1 - Copy the lesson's web address
  WHAT: Open the lesson in your browser. Click once in the bar
  at the very top. The text becomes blue. Press the CTRL key
  and the C key together.
  YOU WILL SEE: nothing. That is fine. The address is copied.

STEP 2 - Open Universal Video Downloader and paste the address
  WHAT: Click the program in the bar at the bottom of the
  screen. Press the blue button "Paste link".
  YOU WILL SEE: the address in the box.
  IF THE BOX IS STILL EMPTY: do step 1 again.

STEP 3 - Open the login page
  WHAT: Look at the very bottom of the window. Click the
  link "Log in to websites".
  YOU WILL SEE: a new page with the title "Log in to websites"
  and a green button "Log in with a password".
  (You can also reach the login window from the button "Log in"
  under the message "No video was found on this page.")

STEP 4 - Open the password window
  WHAT: Click the green button "Log in with a password".
  YOU WILL SEE: a small window "Log in to a course website".

STEP 5 - Check the web address in the first box
  WHAT: Look at the first box. It is filled in for you.
  The address must start with  https://  . (That is the safe
  kind of address. The "s" means the password travels
  protected.)
  YOU WILL SEE: the lesson's address.
  IF IT IS EMPTY OR WRONG: click in the box and paste the
  address with CTRL and V together.

STEP 6 - Type your e-mail or username
  WHAT: Click in the box "E-mail or username:". Type it, the
  same one you use on that website.
  YOU WILL SEE: the letters appear in the box.

STEP 7 - Type your password
  WHAT: Click in the box "Password:". Type it, the same one you
  use on that website.
  YOU WILL SEE: little dots instead of letters. This is normal.
  The dots hide your password from people who look at your
  screen.
  TO CHECK WHAT YOU TYPED: tick the box "Show the password".
  The dots turn into letters. Untick it when you are done.
  Before you press the button, look at the keyboard. Is Caps
  Lock on? Capital and small letters count.

  PASTING INSTEAD OF TYPING: you can paste with CTRL and V
  together. This works also when your keyboard is set to
  Russian. Or right-click in the box and choose "Paste".

STEP 8 - Press "Log in"
  WHAT: Click the green button "Log in".
  YOU WILL SEE: "Logging in - this can take up to about a
  minute. Please wait..."
  WHAT TO DO: wait. Do not click anything. While the login
  runs, the buttons "Cancel" and the X, and the Escape key, do
  not work. The login cannot be stopped half way. Wait up to
  about a minute.

STEP 9 - Success
  YOU WILL SEE: a message like "Logged in to <website>. Now
  press the green "Download video" button."
  WHAT: Press the big green "Download video" button on the
  main screen. Now it works as in section 3.
  IF YOU SEE A RED MESSAGE: read the list "What the messages
  mean" below.

Plain facts about your password:
  * Your e-mail/username and password are sent only to that
    website, and only over a protected (https://) connection.
  * The program does not save your password. It does not write
    it into its log. The password stays in the window until the
    window closes or the login works.
  * A small "login file" stays on this computer, in
    %LOCALAPPDATA%\VideoDownloader\logins . It is like a key to
    your account on that website. Do not send it to anyone.
    After some time the website makes it stop working. Then log
    in again.
  * To remove it: click "Log in to websites", then the button
    "Log out (delete saved logins)". The program asks first.
    YOU WILL SEE: "Logged out: the saved logins were deleted."
    If there was nothing to delete, you see "There are no saved
    logins from this window."
  * Logging out deletes the saved login files on THIS computer
    only. Your login may stay valid on the website's own server
    until you also log out on the website in your browser, or
    until it expires.
  * It works only for lessons that are open for your own
    account.


WHAT THE MESSAGES MEAN, AND WHAT TO DO
--------------------------------------
You see: "No video was found on this page. If it is a private
lesson, log in first (press the button "Log in" below);
otherwise this website may not be supported."
  -> Do this: it may be a private lesson. Press "Log in", or
     follow Option A or B. If you are already logged in and it
     still fails, this website may not be supported. Ask your
     helper.

You see: "This video is private - the website needs to know you
are logged in. Set up "Log in to websites"."
  -> Do this: follow Option A or Option B of this section.

You see: "The website did not accept the e-mail or username, or
the password."
  -> Do this: (1) Tick "Show the password" and check what you
     typed. (2) Check that Caps Lock is off. (3) Open the
     website in your browser and log in there. If that fails
     too, the e-mail or password is wrong: use the website's
     "forgot password" link. (4) Try again.

You see: "Fill in the web address (it starts with https://),
the e-mail or username, and the password."
  -> Do this: one of the three boxes is empty. Fill all three.

You see: "The web address must start with https:// - the
password is never sent over an unprotected connection."
  -> Do this: in the first box, change the beginning of the
     address so that it reads  https://  . Or copy the address
     from the browser again (step 1). If the lesson's address
     in the browser does not start with https://, use option B.

You see: "This does not look like a GetCourse course website.
Use the login file steps on the "Log in to websites" page
instead (the steps with "Open add-on page")."
  -> Do this: your website is not made with GetCourse. Use
     option B below.

You see: "The website asks for a check (CAPTCHA) that this
program cannot do. Use the login file steps ..."
  -> Do this: a CAPTCHA is a test like "I am not a robot" or
     "click all the traffic lights". Only a person can do it.
     Use option B below. The same goes for a code that the
     website sends you in a text message.

You see: "The password was accepted, but the lesson page still
asks you to log in. Check that this lesson is open for your
account on the website."
  -> Do this: your login is fine, but this lesson is not open
     for your account. Open the lesson in your browser. If you
     cannot see it there either, ask the support of the
     website.

You see: "Could not reach the website. Check the internet and
try again."
  -> Do this: check that the internet works (open any web page
     in the browser). Wait a minute. Try again.

You see: "Logged in to <website>, but the lesson page could not
be opened to check it. Press the green "Download video" button
to try."
  -> Do this: press the green "Download video" button. If it
     fails, see the messages above.

You see: "The login worked, but the login file could not be
saved on this computer (disk full or folder not writable)."
  -> Do this: free some space on the disk (delete files you do
     not need, empty the Recycle Bin). Then log in again.

You see: "Logging in did not work. Try once more. If it fails
again, ask your helper to open "Details for helper"."
  -> Do this: try once more. If it fails again, ask your
     helper.

You see: "This video is copy-protected (DRM), like films on
Netflix. Your login is fine ..." (the message goes on: "Watch
it on the website or in its app.")
  -> Do this: nothing is wrong with your login. This video is
     locked on purpose by the service. This program cannot save
     it and does not try to get around the protection. Watch it
     on the website or in its app. This is normal for services
     like Netflix and for many subscription theatre, film and
     sports websites.

You see: "The browser keeps its logins locked. Set up "Log in
to websites" once."
  -> Do this: use option B below.


OPTION B - A LOGIN FILE (ANY WEBSITE)
-------------------------------------
A "login file" is a small file. A free add-on for your browser
makes it. (An add-on is a small extra program inside Chrome or
Edge.) The file tells websites that you are already logged in.
Some people call it "cookies". You make it once. It then works
for weeks or months.

STEP 1 - Open the login page of Universal Video Downloader
  WHAT: At the bottom of the window, click "Log in to
  websites".
  YOU WILL SEE: a page with three steps. Step 1 is "Install the
  free browser add-on", step 2 is "Log in to the websites you
  use", step 3 is "Click the add-on's icon and press "Export"".

STEP 2 - Install the add-on (once)
  WHAT: Next to step 1, click the button "Open add-on page".
  YOU WILL SEE: your browser opens a web page of the add-on
  called "Get cookies.txt LOCALLY".
  WHAT: Click the button "Add to Chrome" (in Chrome) or "Add to
  Edge" (in Edge). A question appears. Confirm it. You may see
  a button like "Add extension".
  YOU WILL SEE: a small puzzle-piece picture at the top right
  of the browser. That is where add-ons live.
  IF YOU DO NOT SEE THE BUTTON: you may already have the
  add-on. Go on to step 3.

STEP 3 - Log in on the website FIRST
  WHAT: Go back to the program. Next to step 2, click the
  button "Open websites". A small window "Open a website and
  log in" opens. Click "Open ..." with the name of your
  website, if it is in the list. Otherwise open your website in
  the browser the way you always do.
  WHAT: Log in on that website, with your e-mail and password.
  Do this for EVERY website you want to download from, one
  after the other, in the same browser.
  YOU WILL SEE: you are logged in on each website, and you can
  see your lessons.
  KEEP THAT TAB OPEN. Do not log out.

STEP 4 - Click the add-on and press "Export"
  WHAT: Stay on the tab of the website where you are logged in.
  Look at the top right of the browser. Click the add-on's
  icon. If you cannot see it, click the puzzle-piece picture
  first. A list of add-ons opens. Click "Get cookies.txt
  LOCALLY".
  YOU WILL SEE: a small window with the add-on's name.
  WHAT: Click the button "Export".
  IMPORTANT: at this moment you must be logged in on the
  website. If you are not, the file is useless.

STEP 5 - The program finds the file by itself
  YOU WILL SEE: in the program, a green message "Login
  file found: ..." (with the file's name). The page lists
  "Login files found on this computer".
  IF YOU DO NOT SEE IT: press "I exported it" (step 3 on that
  page), or press "Look again". If that does not help, press
  "Choose file..." and pick the file. Its name is cookies.txt.
  It is usually in your Downloads folder.
  IF YOU SEE "That file is not a login (cookies.txt) file.":
  you picked the wrong file. Pick the cookies.txt that the
  add-on made.

STEP 6 - Close the website tab. Do NOT log out
  WHAT: Close the tab with the little x. Do NOT click "Log out"
  on the website. Logging out cancels the login file.

STEP 7 - Download
  WHAT: Copy the lesson's address (section 3, step 2) and press
  "Paste link" and the green "Download video" button.

GOOD TO KNOW
  * Do ALL the websites in one go, then export ONCE. One file
    covers every website you were logged in to.
  * After some weeks or months, downloads may fail again. That
    means the login file is old. Repeat steps 3 and 4: log in
    on the website, then click the add-on and press "Export".
  * A login file only proves who you are. It does not unlock
    copy-protected videos (see section 9).
  * To stop using a login file: on the login page, click "Stop
    using" next to it. The program asks first. The file stays
    on your computer.

+-------------------------------------------------------------+
|  SAFETY                                                     |
|                                                             |
|  * Never send your password or a login file to anyone. Not  |
|    by e-mail, not by chat.                                  |
|  * The program asks for your password only in its own       |
|    window "Log in to a course website".                     |
|  * Do not trust a Setup file or zip file from a person you  |
|    do not know. Use only the file from the person who made  |
|    the program for you.                                     |
+-------------------------------------------------------------+


---------------------------------------------------------------
  6. OTHER FEATURES
---------------------------------------------------------------

RECORDING A LIVE WEBINAR ROOM
-----------------------------
Some schools give you a link to a live webinar "room". The web
address contains /room/ , for example
online.example.ru/room/abc . The video is not on that page, so
the normal download cannot get it. The program can record the
broadcast while it runs and turn it into an MP4 file for you.

  1. At the bottom of the window, click
       "Record a webinar room"
  2. Copy the link you received for the webinar. It came in an
     e-mail or is on the course page. It is your own personal
     link: do not share it. Press "Paste link".
  3. Press the green "Start recording". You can do this before
     the webinar begins. The program says "Waiting for the
     broadcast to begin. Keep this window open." and starts
     recording by itself.
  4. Keep the window open. The "Start recording" button turns
     grey and the red "Stop and save" button becomes active.
     The window shows how much has been recorded
     (hours:minutes: seconds). The program asks Windows not to
     go to sleep while it works, but do not close the laptop
     lid and plug in the charger. If the computer sleeps
     anyway, the recording stops or has a gap.
  5. When the webinar is over, the program stops by itself and
     makes the MP4. To finish earlier, press "Stop and save".
     Wait for "Done!". The MP4 is in your download folder.

  * Normally only the ".mp4" is left: the program checks that
    it is as long as the raw recording and then removes the raw
    ".ts" file. If anything looks wrong (pieces missing, a
    different length), it keeps the ".ts" too and the final
    message says so; play the .mp4 before you delete the .ts.
  * If you start late, the program records the broadcast from
    its very beginning, not from the moment you pressed the
    button.
  * If the school sends no video for more than 3 minutes (for
    example a long break, or the broadcast broke off), the
    program decides it is over, saves what it has and stops.
    After a break, start a new recording.
  * The final message says how it ended. If some short pieces
    could not be downloaded, it says so (the video may jump).
  * While the program is only waiting for the broadcast to
    begin, "Stop and save" simply cancels.
  * If you close the window during a recording, the program
    asks first. If you close it anyway, or switch the computer
    off, the recording stops and no MP4 is made. The ".ts" file
    stays in the folder: use "Convert to MP4" on it.
  * This works only for a webinar that is on air now or starts
    soon. A webinar that is already over cannot be recorded.
  * The program needs its helper module (FFmpeg) for the MP4.
    In the Setup version it is already inside.
  * The program uses the personal part of the link only to
    enter the room as you; it does not save it anywhere.
  * A recording is big: about 2 GB per hour. A two-hour webinar
    needs about 4 GB for the raw ".ts" file and about 4 GB more
    for the ".mp4" while it is being made, so keep about 8 GB
    free on the disk.
  * Only rooms whose video comes from the Rutube website are
    supported so far (you cannot tell from the link; just try,
    the program will say so). For another kind it shows a code:
    tell the person who helps you and give them that code.

COURSE PAGES WITH SEVERAL VIDEOS
--------------------------------
Some course websites (for example schools built on GetCourse,
and players called Kinescope) hide their videos inside the
page. Copy the lesson page's address and press the green button
as usual: the program finds the videos itself and downloads all
of them. Each video is saved under its own title when the
player gives one, otherwise as "lesson-name - 1", "lesson-name
- 2", ... For a private lesson, log in first (section 5) -
without a login the page shows no videos at all. The first
message under the link tells how many videos it found. Long
lessons are big files: a lecture of several hours can take a
long time and a lot of disk space.

VK LIVE BROADCASTS
------------------
Links that look like  vkvideo.ru/live-123_456  (a live
broadcast or its recording) work like any other VK video: paste
the link and press the green button. VK sometimes shows a "bot
check" instead when it gets many requests in a row; if that
happens, wait a few minutes and try again.

CONVERTING A RECORDING TO MP4
-----------------------------
If you recorded a live broadcast with another program, the file
is often a ".mkv" or ".ts" file. Some players and phones cannot
open those. Press "Convert to MP4" (below the folder line),
pick the recording, and the program makes a normal .mp4 file
next to it.

  * Picture and sound are copied, not re-made, so there is no
    loss of quality and a long recording takes only a minute or
    two.
  * The original file is never changed or deleted, and an
    existing file is never overwritten (the new one gets "(1)"
    in its name).
  * Do not convert a recording while it is still being
    recorded; wait until the broadcast has ended.

SOUND ONLY (MP3)
----------------
Only want the sound (a lecture, a concert, music)?
  1. On the main screen, above the green button, choose
     "Sound only (MP3)".
  2. The green button now says "Download sound". Press it.
  3. You get a file ending in .mp3 in the same folder as your
     videos. The sound is saved at 192 kbit/s, whatever the
     video quality.
  * The MP3 is made in a second step after the download reaches
    100%; the box says "Almost done - making the MP3 file...
    please wait". Wait for "Done! The sound is saved as an MP3
    file."
  * Sound needs the helper module (FFmpeg). In the Setup
    version it is already inside. If the program still says it
    is missing, press "Install helper" next to the message,
    wait until it says the helper is installed, then press
    "Download sound" again.
  * The choice is not remembered: the program always starts on
    "Video". It applies to this main screen only. The scan page
    and the webinar room page always save video; each page says
    so.

LANGUAGE
--------
The button in the top right corner switches the program between
English and Russian. It shows the name of the OTHER language.
The program remembers your choice. On a computer set up in
Russian the program starts in Russian by itself. You cannot
switch while a download is running.


---------------------------------------------------------------
  7. IF SOMETHING GOES WRONG
---------------------------------------------------------------

Problems are explained in plain words in the box at the bottom
of the window. Often a button next to the message does the fix.
Just press it. Below: what you see, then what to do.
Messages about logging in are in section 5.

THE LINK
--------
You see: "First copy a video's address in your browser, then
press "Paste link"."
  -> Do this: copy the address first (section 3, step 2). Then
     press "Paste link".

You see: "What you copied is not a web address."
  -> Do this: copy the address from the bar at the top of the
     browser.

You see: "This address is not a video page, or this website is
not supported."
  -> Do this: copy the address again. Make sure it is the page
     where the video plays, not the website's front page.

You see: "Please wait - a download is already running."
  -> Do this: wait until the first download is finished.

PRIVATE OR LOCKED VIDEOS
------------------------
You see: "This video is private ..." or "No video was found on
this page."
  -> Do this: section 5 (login).

You see: "This video is copy-protected (DRM) ..."
  -> Do this: nothing is broken, and it is not your login. See
     section 5 and section 9. The program does not try to get
     around the protection.

A WEBSITE STOPPED WORKING
-------------------------
Websites change often. A website that worked yesterday can fail
today. Do these steps, one at a time, until it works:
  1. Close the program. Open it again. Try again.
  2. Press the blue button "Update now" if it is next to the
     message. Or click "Details for helper" at the bottom of
     the window and press "Update download engine". YOU WILL
     SEE: "Updated. Close the program, open it again, and try
     once more." Do that.
  3. Still failing? Ask the person who made the program for a
     new Setup file.

You see: "The update did not work. Check the internet
connection."
  -> Do this: check the internet. Try again in a few minutes.

You see: "No internet connection, or the website is not
answering. Try again in a minute."
  -> Do this: check the internet, wait a minute, press the
     green button again.

You see: "YouTube refused the download. YouTube changes often -
updating the program usually fixes this."
  -> Do this: the three steps above.

You see: "YouTube wants proof you are a person. Log in to
YouTube and set up "Log in to websites"."
  -> Do this: log in to YouTube in your browser, then follow
     option B in section 5.

SEVERAL VIDEOS
--------------
You see: "Done! 2 of 3 videos saved."
  -> One of them failed. The others are saved. Press the green
     button again to retry. Videos that are already saved are
     not downloaded twice.

You see: "None of the videos could be downloaded."
  -> Do this: read the other message in the box. If it is not
     clear, ask your helper to open "Details for helper".

OTHER
-----
You see: "A helper module (FFmpeg) is missing."
  -> Do this: press "Install helper" and wait a few minutes. In
     the Setup version the module is already inside, so if you
     see this message, ask your helper.

You see: "Secure-connection problem."
  -> Do this: ask your helper to look at "Details for helper".

You see: "Something went wrong. Your helper can see the details
under "Details for helper"."
  -> Do this: click "Details for helper" at the bottom of the
     window. It shows what works, the versions, and a log of
     what the program did. Show it to the person who helps you.

The download stops partway
  -> Usually the internet connection. Press the green button
     again; it picks up from where it stopped.

Videos look blurrier than expected
  -> That is normal. This tool saves 480p on purpose, so files
     stay small.

The program does not open at all
  -> Start it from the Desktop picture or from the Start menu
     (section 2). If it still does not open, ask your helper
     and tell them what you saw on the screen.

FOR YOUR HELPER
---------------
The log file is
    %LOCALAPPDATA%\VideoDownloader\VideoDownloader.log
Copy that path (the line above), paste it into the address bar
of any folder window and press Enter.
The Setup version is a windowed program. It has no command-line
self test. "Details for helper" shows the system status
instead.


---------------------------------------------------------------
  8. IS IT ALL RIGHT TO DOWNLOAD THIS?
---------------------------------------------------------------

This program is a tool, like a video recorder. What you may do
with a recording depends on the video, the website and the law
of your country - and it is your own responsibility. The rules
below are general guidance, not legal advice.

  * Saving a video for your own private viewing (to watch
    without internet, to study a course you have paid for or
    been given access to) is what this program is made for. In
    some countries the law allows such private copies; in
    others it does not. "Fair use" is a United States rule and
    does not apply everywhere.
  * Use the program only for your own private use. Do not
    publish, sell or share what you save, and do not upload it
    to another website. The video still belongs to whoever made
    it.
  * Use only your own login. Never use another person's login
    file, and never pass your own login file on.
  * The program does not break copy protection. If a video is
    encrypted, it simply fails (see section 9).
  * The terms of use of a website often forbid downloading.
    Recording a webinar can break the rules of the school that
    runs it. You are responsible for what you download or
    record. If in doubt, ask the owner of the video for
    permission.
  * The program is provided "as is", without any warranty of
    any kind. You use it at your own risk.
  * The program is not connected to, and not approved by,
    YouTube, VK, Vimeo, GetCourse, Kinescope or any other
    website named here. The names belong to their owners.


---------------------------------------------------------------
  9. WHAT IT CANNOT DO
---------------------------------------------------------------

  * Copy-protected (DRM) videos cannot be saved. Netflix,
    Disney+, Amazon Prime and similar services lock their
    videos on purpose. This program cannot save them and does
    not try to get around the protection. Nothing is broken.
    The same is true for many subscription theatre, film and
    sports sites: if the program says "This video is
    copy-protected (DRM)", your login is fine, but this program
    cannot save the video.
  * It always downloads in 480p. There is no setting for higher
    quality.
  * A website can change overnight and stop working until the
    download engine catches up (usually within days). Closing
    and opening the program the next day often fixes it.
  * Windows only. There is no version for Mac or Linux.
  * Webinar rooms: only rooms whose video comes from Rutube,
    and only while you keep the window open and the computer
    awake. It cannot record a room whose link has expired or
    that needs a password you do not have. A webinar that has
    already ended and was not recorded by the school cannot be
    recovered.


---------------------------------------------------------------
  10. FILES AND FOLDERS
---------------------------------------------------------------

Where things are (you never need to open these by hand). The
Setup version has no VideoDownloader.bat: you start it from the
Desktop picture or the Start menu.

  THE PROGRAM FOLDER (put there by the Setup, with a copy
  of this README.txt):
      %LOCALAPPDATA%\Programs\Universal Video Downloader
  YOUR VIDEOS: the Downloads folder, or the folder you
  chose with "Change" on the main screen.
  THE SETTINGS FILE (your download folder and language):
      .video_downloader.json  in your user folder
  THE LOG FILE (messages for troubleshooting):
      %LOCALAPPDATA%\VideoDownloader\VideoDownloader.log
  SAVED LOGINS (made by "Log in with a password"):
      %LOCALAPPDATA%\VideoDownloader\logins
  THE ENGINE UPDATE FOLDER (the newer download engine that
  the program fetched by itself):
      %LOCALAPPDATA%\VideoDownloader\engine

WHAT UNINSTALLING REMOVES: the program, the saved logins and
the engine update folder. It does not remove your downloaded
videos. The settings file and the log file stay.

The zip version uses the same data folder,
%LOCALAPPDATA%\VideoDownloader. If you used both versions,
uninstalling the Setup also deletes the saved logins of the zip
version.


---------------------------------------------------------------
  QUICK REFERENCE
---------------------------------------------------------------

  Start the program .... Desktop picture "Universal Video
                         Downloader", or Windows key, type
                         Universal , Enter
  Download a video ..... copy the address, "Paste link", green
                         "Download video"
  Find your videos ..... "Open folder" button, or the Downloads
                         folder
  A website stopped .... close and reopen the program; then
                         "Update now"; then ask for a new Setup
  Need a login ......... "Log in to websites" (section 5)
  Uninstall ............ Settings > Apps > Installed apps >
                         Universal Video Downloader > Uninstall


---------------------------------------------------------------
  WORDS EXPLAINED
---------------------------------------------------------------

  Link / address .. the text in the bar at the top of your
                    browser. It starts with https://
  https:// ........ the safe kind of web address. Nobody can
                    read what travels between you and the site.
  Setup ........... the one file you double-click to put the
                    program on your computer.
  Download engine . the part of the program that knows how to
                    get a video from each website. Websites
                    change, so it is refreshed from time to
                    time.
  Helper module ... FFmpeg: a small tool that joins picture and
                    sound and makes MP3 and MP4 files.
  Login file ...... also called "cookies": a small file that
                    tells a website you are already logged in,
                    so it does not ask again. Treat it like a
                    key to your account.
  Add-on .......... a small extra program inside your browser.
  GetCourse ....... a platform that many online schools use.
                    You can tell it by "/teach/" in the web
                    address of the lesson.
  Old name ........ the program used to be called "Video
                    Downloader". Old copies show that name.
  Helper (person) . a family member or friend who helps you
                    with the computer.


---------------------------------------------------------------
  APPENDIX: THE OLDER WAY TO INSTALL (ZIP FILE)
---------------------------------------------------------------

Use this only if you cannot use the Setup file. The Setup way
(section 2) is simpler. Do not use both on the same computer.

This way needs the internet on the first run, and it installs
Python by itself.

  1. Unzip UniversalVideoDownloader.zip into a folder of your
     own, for example  Documents\VideoDownloader\ . Do not run
     it from inside the zip file. The folder holds three files:
         VideoDownloader.bat    <- the one you double-click
         VideoDownloader.py     <- the program itself
         README.txt             <- this file
     They must stay together in the SAME folder.
  2. Double-click VideoDownloader.bat. A black window walks
     through four checks:
         [1 of 4]  Looking for Python...
         [2 of 4]  Checking the download engine...
         [3 of 4]  Checking secure connections...
         [4 of 4]  Checking the helper module (FFmpeg)...
     If Python is missing it asks "Install Python now [Y,N]?".
     Press  Y  and Enter, and wait a few minutes. Do not close
     the window. When all four checks pass, the Video
     Downloader window opens. The first run takes a few
     minutes; later runs take a few seconds.
  3. If it says "Please RESTART THE COMPUTER, then double-click
     this launcher again.", restart the computer and
     double-click VideoDownloader.bat again. This happens at
     most once.
  4. Optional Desktop icon: right-click VideoDownloader.bat,
     (on Windows 11 choose "Show more options"), then "Send to"
     -> "Desktop (create shortcut)".

In this version the program updates its download engine each
time you start it. A helper can run a self test: hold SHIFT,
right-click the folder, choose "Open PowerShell window here" or
"Open command window here", type
    .\VideoDownloader.bat --selftest
and send the text it prints to the person helping you. One
video without a window: .\VideoDownloader.bat --url "LINK"
(zip version only).

The zip version and the Setup version share the same data
folder, %LOCALAPPDATA%\VideoDownloader. If you used both,
uninstalling the Setup also deletes the saved logins of the zip
version.

===============================================================
