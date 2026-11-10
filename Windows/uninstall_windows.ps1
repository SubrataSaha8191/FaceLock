<#
 Removes FaceLock's shortcuts and stops the service.

   powershell -ExecutionPolicy Bypass -File Windows\uninstall_windows.ps1
   powershell -ExecutionPolicy Bypass -File Windows\uninstall_windows.ps1 -RemoveData   # also deletes face data

 NOTE: this script has not been run on a real Windows machine yet.
#>
param([switch]$RemoveData)

$programs = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
foreach ($f in @((Join-Path $programs "FaceLock.lnk"), (Join-Path $programs "Startup\FaceLock Service.lnk"))) {
    if (Test-Path $f) { Remove-Item $f -Force; Write-Host "Removed $f" }
}

# Stop the running service (match on the script it runs)
Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe' OR Name = 'python.exe'" |
    Where-Object { $_.CommandLine -like "*Service*main.py*" -or $_.CommandLine -like "*auth_service.py*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host "Stopped service (PID $($_.ProcessId))" }

if ($RemoveData) {
    $data = Join-Path $env:LOCALAPPDATA "FaceLock"
    if (Test-Path $data) { Remove-Item $data -Recurse -Force; Write-Host "Deleted $data" }
} else {
    Write-Host "Your face data was kept in $env:LOCALAPPDATA\FaceLock (use -RemoveData to delete it)."
}
