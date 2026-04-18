$ErrorActionPreference = "Continue"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot ".runtime"

function Stop-ManagedProcess {
    param(
        [string]$Name,
        [string]$PidFile
    )

    if (-not (Test-Path $PidFile)) {
        return $false
    }

    $rawPid = Get-Content -Path $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    $pidValue = 0

    if (-not [int]::TryParse($rawPid, [ref]$pidValue)) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return $false
    }

    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped $Name (PID $pidValue)."
    } else {
        Write-Host "$Name tidak aktif."
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    return $true
}

$anyStopped = $false

if (Stop-ManagedProcess -Name "Frontend" -PidFile (Join-Path $runtimeDir "frontend.pid")) {
    $anyStopped = $true
}

if (Stop-ManagedProcess -Name "Backend" -PidFile (Join-Path $runtimeDir "backend.pid")) {
    $anyStopped = $true
}

if (Stop-ManagedProcess -Name "MongoDB" -PidFile (Join-Path $runtimeDir "mongo.pid")) {
    $anyStopped = $true
}

# Fallback by port in case child process still listens after parent stop.
$ports = @(3000, 8000, 27017)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    $processIds = @($connections | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($processId in $processIds) {
        if ($processId -le 0) {
            continue
        }

        $stopped = $false

        try {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            $stopped = $true
        } catch {
            cmd /c "taskkill /PID $processId /F /T" | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $stopped = $true
            }
        }

        if ($stopped) {
            Write-Host "Stopped process on port $port (PID $processId)."
            $anyStopped = $true
        }
    }

}

# Additional cleanup for uvicorn reload workers that can remain alive after parent exits.
$backendStillListening = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($backendStillListening) {
    $pythonCandidates = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -match '^python(3\.12)?\.exe$' -or $_.Name -eq 'py.exe') -and
        ($_.CommandLine -match 'uvicorn' -or $_.CommandLine -match 'server:app' -or $_.CommandLine -match 'multiprocessing\.spawn')
    }

    foreach ($candidate in $pythonCandidates) {
        $candidatePid = [int]$candidate.ProcessId
        try {
            Stop-Process -Id $candidatePid -Force -ErrorAction Stop
            Write-Host "Stopped backend Python process (PID $candidatePid)."
            $anyStopped = $true
        } catch {
            cmd /c "taskkill /PID $candidatePid /F /T" | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Stopped backend Python process (PID $candidatePid) via taskkill."
                $anyStopped = $true
            }
        }
    }

    $backendStillListening = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($backendStillListening) {
        $remaining = @($backendStillListening | Select-Object -ExpandProperty OwningProcess -Unique) -join ","
        Write-Warning "Backend masih aktif pada port 8000 (PID: $remaining)."
    }
}

$remainingPorts = @()
foreach ($port in $ports) {
    $stillListening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($stillListening) {
        $remainingPids = @($stillListening | Select-Object -ExpandProperty OwningProcess -Unique) -join ","
        $remainingPorts += "${port} (PID: $remainingPids)"
    }
}

if ($remainingPorts.Count -gt 0) {
    Write-Warning ("Masih ada port aktif: " + ($remainingPorts -join "; "))
}

if (-not $anyStopped) {
    Write-Host "Tidak ada service ProManage yang aktif."
}