# Builds the Windows Setup program of the Universal Video Downloader: a PyInstaller ONE-FOLDER build of
# VideoDownloader.py (windowed, with yt-dlp, truststore and FFmpeg inside), wrapped by an Inno Setup program.
# Command: powershell -NoProfile -ExecutionPolicy Bypass -File build_installer.ps1 [-Dest <folder>] [-Work <folder>]
# Output:  <Dest>\UniversalVideoDownloader-Setup.exe
#          (default Dest: the folder dist next to this script, next to the release zip)
#
# Needs on this PC: Python 3.11+ on PATH (with pip and internet, to fetch PyInstaller, yt-dlp, truststore and
# imageio-ffmpeg into a private build environment) and Inno Setup 6 (ISCC.exe).
# Inno Setup: winget install -e --id JRSoftware.InnoSetup --scope user
# Nothing is installed system-wide. The release zip (build_release.ps1) is a separate product.
#
# Steps (any failure stops the build and leaves an existing Setup file untouched):
#   1. the offline tests must pass (tests\test_room.py, test_audio.py, test_login.py)
#   2. README.txt "version X.Y" must equal APP_VER in VideoDownloader.py
#   3. ISCC.exe is found; the installer script and this script are ASCII + CRLF
#   4. a private build environment is created in the work folder; the packages are installed in it
#   5. PyInstaller builds the one-folder program (windowed, logo icon)
#   6. the built folder is checked (exe, FFmpeg, yt-dlp present; no private or development file in it)
#   7. Inno Setup compiles UniversalVideoDownloader-Setup.exe
#   8. the Setup file is checked and moved to <Dest>
# -Work <folder>: keep the work folder there and reuse it next time (faster). Without it a temporary
# folder is used and deleted at the end.
param(
    [string]$Dest = (Join-Path $PSScriptRoot "dist"),
    [string]$Work = ""
)

$ErrorActionPreference = "Stop"
$src = $PSScriptRoot
$setupName = "UniversalVideoDownloader-Setup.exe"
$pyInstallerVersion = "6.22.3"
$privateNames = @("CLAUDE.md", "build_release.ps1", "build_installer.ps1", ".gitignore", ".gitattributes", "room_socket.py")
$privateDirs = @("tests", "installer", ".git", "venv", ".venv", "selftest_downloads")

function Test-AsciiCrlf([string]$path, [string]$label) {
    $problems = @()
    $b = [System.IO.File]::ReadAllBytes($path)
    for ($i = 0; $i -lt $b.Length; $i++) { if ($b[$i] -gt 127) { $problems += "$label has a non-ASCII byte at offset $i"; break } }
    for ($i = 0; $i -lt $b.Length; $i++) {
        if ($b[$i] -eq 10 -and ($i -eq 0 -or $b[$i - 1] -ne 13)) { $problems += "$label has a line end without CR at offset $i"; break }
        if ($b[$i] -eq 13 -and ($i + 1 -ge $b.Length -or $b[$i + 1] -ne 10)) { $problems += "$label has a lone CR at offset $i"; break }
    }
    return $problems
}

# Runs a native command through cmd so that stderr text does not become a PowerShell error in 5.1.
function Invoke-Native([string]$commandLine, [string]$failMessage) {
    cmd /c "$commandLine 2>&1" | Out-Host
    if ($LASTEXITCODE -ne 0) { throw $failMessage }
}

$keepWork = [bool]$Work
if (-not $Work) { $Work = Join-Path $env:TEMP ("UniversalVideoDownloader_installer_" + [guid]::NewGuid().ToString("N").Substring(0, 8)) }
$tmpSetup = $null
$failed = $false

try {
    Write-Host "[1/8] Running the tests..."
    Push-Location $src
    try {
        if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python was not found on PATH - installer not built." }
        foreach ($t in (@("test_room.py", "test_audio.py", "test_login.py", "test_scan.py", "test_engine.py", "test_texts.py", "test_webinar.py") + @(if (Test-Path "tests\test_shipped.py") { "test_shipped.py" }))) {
            cmd /c "python -W ignore tests\$t 2>&1" | Out-Host
            if ($LASTEXITCODE -ne 0) { throw "tests\$t failed - installer not built." }
        }
    } finally { Pop-Location }

    Write-Host "[2/8] Checking the version..."
    $py = [System.IO.File]::ReadAllText((Join-Path $src "VideoDownloader.py"), [System.Text.Encoding]::UTF8)
    $m = [regex]::Match($py, 'APP_VER\s*=\s*"([^"]+)"')
    if (-not $m.Success) { throw "APP_VER not found in VideoDownloader.py." }
    $appVer = $m.Groups[1].Value
    $head = [System.IO.File]::ReadAllLines((Join-Path $src "README.txt"), [System.Text.Encoding]::UTF8) | Select-Object -First 5
    if (-not (($head -join "`n") -match "version $([regex]::Escape($appVer))\b")) { throw "README.txt header does not say 'version $appVer'." }
    Write-Host "      version $appVer in code and README.txt"

    Write-Host "[3/8] Looking for Inno Setup and checking the script files..."
    $iscc = $null
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { $iscc = $cmd.Source }
    if (-not $iscc) {
        foreach ($c in @((Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"), (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"), (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"))) {
            if ($c -and (Test-Path -LiteralPath $c)) { $iscc = $c; break }
        }
    }
    if (-not $iscc) { throw "Inno Setup 6 (ISCC.exe) was not found. Install it with:  winget install -e --id JRSoftware.InnoSetup --scope user" }
    $iss = Join-Path $src "installer\UniversalVideoDownloader.iss"
    if (-not (Test-Path -LiteralPath $iss)) { throw "installer\UniversalVideoDownloader.iss is missing." }
    $bp = @()
    $bp += Test-AsciiCrlf $iss "installer\UniversalVideoDownloader.iss"
    $bp += Test-AsciiCrlf (Join-Path $src "build_installer.ps1") "build_installer.ps1"
    if ($bp.Count -gt 0) { throw ("Byte check failed:`r`n  " + ($bp -join "`r`n  ")) }
    if (-not (Test-Path -LiteralPath (Join-Path $src "THIRD-PARTY-NOTICES.txt"))) { throw "THIRD-PARTY-NOTICES.txt is missing." }
    foreach ($need in @("LICENSE", "README_RU.txt")) { if (-not (Test-Path -LiteralPath (Join-Path $src $need))) { throw "$need is missing." } }
    $ico = Join-Path $src "installer\logo.ico"
    if (-not (Test-Path -LiteralPath $ico)) { throw "installer\logo.ico is missing." }

    Write-Host "[4/8] Preparing the private build environment (PyInstaller $pyInstallerVersion, yt-dlp, truststore, imageio-ffmpeg)..."
    New-Item -ItemType Directory -Force -Path $Work | Out-Null
    $envDir = Join-Path $Work "buildenv"
    $bpy = Join-Path $envDir "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $bpy)) { Invoke-Native "python -m venv `"$envDir`"" "Could not create the build environment." }
    Invoke-Native "`"$bpy`" -m pip install --disable-pip-version-check -q -U pyinstaller==$pyInstallerVersion `"yt-dlp[default]`" truststore imageio-ffmpeg" "pip could not install the packages (internet needed)."
    Invoke-Native "`"$bpy`" -c `"import tkinter, yt_dlp, truststore, imageio_ffmpeg`"" "The build environment cannot import tkinter, yt_dlp, truststore and imageio_ffmpeg."

    Write-Host "[5/8] Building the program folder with PyInstaller (a few minutes)..."
    $dist = Join-Path $Work "dist"; $pwork = Join-Path $Work "pybuild"; $spec = Join-Path $Work "spec"
    foreach ($d in @($dist, $pwork, $spec)) { if (Test-Path $d) { Remove-Item $d -Recurse -Force } }
    $pyArgs = "-m PyInstaller --noconfirm --clean --windowed --onedir --name VideoDownloader --icon `"$ico`" " +
            "--collect-all yt_dlp --collect-all yt_dlp_ejs --collect-all imageio_ffmpeg --collect-all certifi --exclude-module mutagen " +
            "--hidden-import truststore --distpath `"$dist`" --workpath `"$pwork`" --specpath `"$spec`" `"$(Join-Path $src 'VideoDownloader.py')`""
    Invoke-Native "`"$bpy`" $pyArgs" "PyInstaller failed."

    Write-Host "[6/8] Checking the built program folder..."
    $app = Join-Path $dist "VideoDownloader"
    if (-not (Test-Path -LiteralPath (Join-Path $app "VideoDownloader.exe"))) { throw "PyInstaller did not produce VideoDownloader.exe." }
    $all = Get-ChildItem -LiteralPath $app -Recurse -Force -File
    if (-not ($all | Where-Object { $_.Name -like "ffmpeg*.exe" })) { throw "FFmpeg is not inside the built program." }
    if (-not ($all | Where-Object { $_.FullName -like "*yt_dlp*" })) { throw "yt-dlp is not inside the built program." }
    if ($all | Where-Object { $_.FullName -like "*\mutagen\*" }) { throw "mutagen (GPL) is inside the built program: it must stay out." }
    $problems = @()
    $appFull = (Resolve-Path $app).Path.TrimEnd('\')
    foreach ($file in $all) {
        $rel = $file.FullName.Substring($appFull.Length + 1)
        $parts = $rel.Split('\')
        # our own files: at the top level only (libraries inside _internal have test folders and a cookies.py of their own)
        if ($parts.Length -eq 1 -and $privateNames -contains $file.Name) { $problems += "private/development file in the program folder: $rel" }
        if ($file.Name -like "*cookies*.txt") { $problems += "cookie file in the program folder: $rel" }
        if ($parts.Length -gt 1 -and $parts[0] -ne "_internal" -and $privateDirs -contains $parts[0]) { $problems += "development folder in the program folder: $rel" }
    }
    if ($problems.Count -gt 0) { throw ("Unsafe program folder content:`r`n  " + ($problems -join "`r`n  ")) }
    $mb = [math]::Round((($all | Measure-Object Length -Sum).Sum) / 1MB, 1)
    Write-Host "      $($all.Count) files, $mb MB; exe, FFmpeg and yt-dlp present, no private file"

    Write-Host "[7/8] Compiling the Setup program with Inno Setup..."
    $outDir = Join-Path $Work "setup"
    if (Test-Path $outDir) { Remove-Item $outDir -Recurse -Force }
    New-Item -ItemType Directory -Path $outDir | Out-Null
    Invoke-Native "`"$iscc`" /Qp `"/O$outDir`" `"/DAppVer=$appVer`" `"/DSourceDir=$app`" `"/DProjectDir=$src`" `"$iss`"" "Inno Setup failed."

    Write-Host "[8/8] Checking and writing the Setup file..."
    $built = Join-Path $outDir $setupName
    if (-not (Test-Path -LiteralPath $built)) { throw "Inno Setup did not produce $setupName." }
    $size = (Get-Item -LiteralPath $built).Length
    if ($size -lt 20MB) { throw "The Setup file is suspiciously small ($size bytes)." }
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    $final = Join-Path (Resolve-Path $Dest).Path $setupName
    $tmpSetup = $final + ".tmp"
    Copy-Item -LiteralPath $built -Destination $tmpSetup -Force
    if (Test-Path $final) { Remove-Item $final -Force }
    Move-Item -LiteralPath $tmpSetup -Destination $final
    $tmpSetup = $null
    Write-Host ""
    Write-Host "Installer built: $final"
    Write-Host ("  {0:N1} MB, version {1}" -f ($size / 1MB), $appVer)
}
catch {
    Write-Host ""
    Write-Host "BUILD FAILED: $($_.Exception.Message)" -ForegroundColor Red
    if ($tmpSetup -and (Test-Path $tmpSetup)) { Remove-Item $tmpSetup -Force -ErrorAction SilentlyContinue }
    $failed = $true
}
finally {
    if (-not $keepWork -and (Test-Path $Work)) { Remove-Item $Work -Recurse -Force -ErrorAction SilentlyContinue }
}
if ($failed) { exit 1 }
