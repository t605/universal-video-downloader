; Inno Setup script for the Universal Video Downloader Setup program. ASCII only.
; Do not compile this by hand: build_installer.ps1 builds the PyInstaller folder first and passes the defines:
;   /DAppVer=<version>        version (same as APP_VER in VideoDownloader.py)
;   /DSourceDir=<folder>     the PyInstaller one-folder output (contains VideoDownloader.exe)
;   /DProjectDir=<folder>    the project folder (README.txt, installer\logo.ico)
;
; What the Setup does:
;   - installs the program for the CURRENT USER only (no administrator rights) into
;     %LOCALAPPDATA%\Programs\Universal Video Downloader (fixed: no folder page), with a Start menu entry
;     and a desktop icon (ticked by default).
;   - nothing else has to be installed: Python, the download engine and FFmpeg are inside.
;   - the Setup can show English or Russian (it may ask once, in a small language window).
;   - an installation over an older one also removes the downloaded engine update (the new program
;     has its own, newer engine).
;   - the uninstaller removes the program AND the saved logins and the downloaded engine update
;     (%LOCALAPPDATA%\VideoDownloader\logins and \engine: the logins are keys to accounts).
;     The settings file and the log stay.
#ifndef AppVer
  #error AppVer is not defined. Build with build_installer.ps1.
#endif
#ifndef SourceDir
  #error SourceDir is not defined. Build with build_installer.ps1.
#endif
#ifndef ProjectDir
  #error ProjectDir is not defined. Build with build_installer.ps1.
#endif

[Setup]
AppId={{B3E7A1D4-5C2F-4E8A-9D16-7A0C4F2B8E35}
AppName=Universal Video Downloader
AppVersion={#AppVer}
AppVerName=Universal Video Downloader {#AppVer}
AppPublisher=Michael Yeruhimovich
DefaultDirName={localappdata}\Programs\Universal Video Downloader
DisableDirPage=yes
DefaultGroupName=Universal Video Downloader
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
MinVersion=10.0
SetupLogging=yes
AppPublisherURL=https://github.com/t605/universal-video-downloader
AppSupportURL=https://github.com/t605/universal-video-downloader/issues
VersionInfoVersion={#AppVer}.0.0
VersionInfoCompany=Michael Yeruhimovich
VersionInfoDescription=Universal Video Downloader Setup
VersionInfoProductName=Universal Video Downloader
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputBaseFilename=UniversalVideoDownloader-Setup
SetupIconFile={#ProjectDir}\installer\logo.ico
UninstallDisplayIcon={app}\VideoDownloader.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "{#ProjectDir}\README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectDir}\THIRD-PARTY-NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectDir}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectDir}\README_RU.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectDir}\installer\logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Universal Video Downloader"; Filename: "{app}\VideoDownloader.exe"; AppUserModelID: "MY.VideoDownloader"
Name: "{autoprograms}\Universal Video Downloader - Read me"; Filename: "{app}\README.txt"
Name: "{autoprograms}\Universal Video Downloader - Read me (Russian)"; Filename: "{app}\README_RU.txt"
Name: "{autodesktop}\Universal Video Downloader"; Filename: "{app}\VideoDownloader.exe"; AppUserModelID: "MY.VideoDownloader"; Tasks: desktopicon

[Run]
Filename: "{app}\VideoDownloader.exe"; Description: "{cm:LaunchProgram,Universal Video Downloader}"; Flags: nowait postinstall skipifsilent

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{localappdata}\VideoDownloader\engine"

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\VideoDownloader\logins"
Type: filesandordirs; Name: "{localappdata}\VideoDownloader\engine"
