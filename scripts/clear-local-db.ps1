$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$dataDb = Join-Path $repoRoot "data\db"
$dataLog = Join-Path $repoRoot "data\log"

# Ensure processes are stopped before deleting files.
powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "stop-dev.ps1")

if (Test-Path $dataDb) {
    Get-ChildItem -Path $dataDb -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

if (Test-Path $dataLog) {
    Get-ChildItem -Path $dataLog -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Data MongoDB lokal berhasil dikosongkan."
