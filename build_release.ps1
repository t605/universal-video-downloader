# Builds the release zip from a whitelist of files. ASCII-only file.
# Usage:  powershell -ExecutionPolicy Bypass -File build_release.ps1
# Output: the folder dist next to this script\UniversalVideoDownloader.zip
#         (-Dest <folder> builds somewhere else, e.g. for a trial build)
param([string]$Dest = (Join-Path $PSScriptRoot "dist"))
$ErrorActionPreference = "Stop"
$src = $PSScriptRoot
$zip = Join-Path $Dest "UniversalVideoDownloader.zip"
$files = "VideoDownloader.bat", "VideoDownloader.py", "README.txt", "README_RU.txt", "LICENSE"

# 1. checks (compile, offline tests of room / audio / login, version, ASCII; the rest is manual - see CLAUDE.md)
foreach ($f in $files) {
    if (-not (Test-Path (Join-Path $src $f))) { throw "Missing file: $f" }
}
# run through cmd: Windows PowerShell 5.1 turns python's stderr into errors
# (compile() in memory, so no __pycache__ is left in the project)
$env:VD_SRC = Join-Path $src "VideoDownloader.py"
cmd /c "python -c `"import os; compile(open(os.environ['VD_SRC'], encoding='utf-8').read(), 'VideoDownloader.py', 'exec')`" 2>&1" | Out-Host
if ($LASTEXITCODE -ne 0) { throw "VideoDownloader.py does not compile - release not built." }

# offline tests (fake servers on this PC): room recorder ~11 s, sound-only options, school login
Push-Location $src
cmd /c "python -W ignore tests\test_room.py 2>&1" | Out-Host
$testCode = $LASTEXITCODE
if ($testCode -eq 0) {
    cmd /c "python -W ignore tests\test_audio.py 2>&1" | Out-Host
    $testCode = $LASTEXITCODE
}
if ($testCode -eq 0) {
    cmd /c "python -W ignore tests\test_login.py 2>&1" | Out-Host
    $testCode = $LASTEXITCODE
}
if ($testCode -eq 0) {
    cmd /c "python -W ignore tests\test_scan.py 2>&1" | Out-Host
    $testCode = $LASTEXITCODE
}
if ($testCode -eq 0) {
    cmd /c "python -W ignore tests\test_engine.py 2>&1" | Out-Host
    $testCode = $LASTEXITCODE
}
if ($testCode -eq 0) {
    cmd /c "python -W ignore tests\test_texts.py 2>&1" | Out-Host
    $testCode = $LASTEXITCODE
}
if ($testCode -eq 0) {
    cmd /c "python -W ignore tests\test_webinar.py 2>&1" | Out-Host
    $testCode = $LASTEXITCODE
}
if ($testCode -eq 0 -and (Test-Path "tests\test_shipped.py")) {   # private check (not in the public copy)
    cmd /c "python -W ignore tests\test_shipped.py 2>&1" | Out-Host
    $testCode = $LASTEXITCODE
}
Pop-Location
if ($testCode -ne 0) { throw "tests\test_room.py, test_audio.py, test_login.py, test_scan.py, test_engine.py, test_texts.py or test_webinar.py failed - release not built." }

$py = Get-Content (Join-Path $src "VideoDownloader.py") -Raw -Encoding UTF8
if ($py -notmatch 'APP_VER\s*=\s*"([^"]+)"') { throw "APP_VER not found in VideoDownloader.py" }
$ver = $Matches[1]
$head = Get-Content (Join-Path $src "README.txt") -TotalCount 5
if (-not ($head -match "version $([regex]::Escape($ver))\b")) {
    throw "README.txt header does not say 'version $ver' - update it first."
}

$bat = [IO.File]::ReadAllBytes((Join-Path $src "VideoDownloader.bat"))
if ($bat | Where-Object { $_ -gt 127 }) { throw "VideoDownloader.bat contains non-ASCII characters." }

# 2. copy the whitelisted files to a staging folder
$stage = Join-Path $env:TEMP "UniversalVideoDownloader_release"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage | Out-Null
foreach ($f in $files) { Copy-Item (Join-Path $src $f) $stage }

# 3. safety check: nothing private or development-only
$bad = Get-ChildItem $stage -Recurse -File | Where-Object {
    $_.Name -like "*cookies*" -or $_.Extension -in ".skill", ".zip", ".md", ".json" -or
    $_.FullName -like "*__pycache__*" }
if ($bad) { throw "Private or development file in release: $($bad.FullName -join ', ')" }

# 4. zip (replaces the previous release zip)
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path "$stage\*" -DestinationPath $zip
Remove-Item $stage -Recurse -Force
Write-Host "Release built: $zip  (version $ver)"
