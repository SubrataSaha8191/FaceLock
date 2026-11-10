<#
 FaceLock installer for Windows (per user, no administrator rights needed).

   powershell -ExecutionPolicy Bypass -File Windows\install_windows.ps1
   powershell -ExecutionPolicy Bypass -File Windows\install_windows.ps1 -NoAutostart

 What it does:
   1. creates .venv and installs FaceLock into it
   2. downloads and verifies the face models
   3. adds a Start Menu shortcut for the dashboard
   4. (unless -NoAutostart) starts the unlock service automatically when you sign in

 NOTE: this script has not been run on a real Windows machine yet.
#>
param([switch]$NoAutostart)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Find Python 3.9+
$python = $null
foreach ($candidate in @("py -3", "python")) {
    try {
        $v = & cmd /c "$candidate --version 2>&1"
        if ($v -match "Python 3\.(\d+)" -and [int]$Matches[1] -ge 9) { $python = $candidate; break }
    } catch { }
}
if (-not $python) { throw "Python 3.9 or newer is required. Install it from https://www.python.org/downloads/" }

Write-Host "Creating virtual environment..."
& cmd /c "$python -m venv .venv"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$venvPythonw = Join-Path $root ".venv\Scripts\pythonw.exe"

Write-Host "Installing FaceLock..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e .

Write-Host "Fetching face models..."
& $venvPython Scripts\fetch_models.py

$shell = New-Object -ComObject WScript.Shell
$programs = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"

# Dashboard shortcut (pythonw = no console window)
$link = $shell.CreateShortcut((Join-Path $programs "FaceLock.lnk"))
$link.TargetPath = $venvPythonw
$link.Arguments = "`"$root\Dashboard\main.py`""
$link.WorkingDirectory = $root
$link.Description = "FaceLock"
$link.Save()

if (-not $NoAutostart) {
    $startup = Join-Path $programs "Startup"
    $svc = $shell.CreateShortcut((Join-Path $startup "FaceLock Service.lnk"))
    $svc.TargetPath = $venvPythonw
    $svc.Arguments = "`"$root\Service\main.py`""
    $svc.WorkingDirectory = $root
    $svc.WindowStyle = 7   # minimised
    $svc.Description = "FaceLock unlock service"
    $svc.Save()
    # Start it now so you don't have to sign out first
    Start-Process -FilePath $venvPythonw -ArgumentList "`"$root\Service\main.py`"" -WorkingDirectory $root -WindowStyle Hidden
}

Write-Host ""
Write-Host "Done. Open FaceLock from the Start Menu, enroll your face, then use Unlock > Test unlock."
Write-Host "Face data and logs live in $env:LOCALAPPDATA\FaceLock"
