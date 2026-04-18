param(
    [switch]$SkipMongo,
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$BackendReload
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot ".runtime"
$dataDb = Join-Path $repoRoot "data\db"
$dataLog = Join-Path $repoRoot "data\log"
$mongoExe = Join-Path $repoRoot "tools\mongodb\mongodb-win32-x86_64-windows-8.2.7\bin\mongod.exe"
$mongoLog = Join-Path $dataLog "mongod.log"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
New-Item -ItemType Directory -Path $dataDb -Force | Out-Null
New-Item -ItemType Directory -Path $dataLog -Force | Out-Null

$backendEnv = Join-Path $repoRoot "backend\.env"
$backendEnvExample = Join-Path $repoRoot "backend\.env.example"
$frontendEnv = Join-Path $repoRoot "frontend\.env"
$frontendEnvExample = Join-Path $repoRoot "frontend\.env.example"

if (-not (Test-Path $backendEnv) -and (Test-Path $backendEnvExample)) {
    Copy-Item $backendEnvExample $backendEnv
}

if (-not (Test-Path $frontendEnv) -and (Test-Path $frontendEnvExample)) {
    Copy-Item $frontendEnvExample $frontendEnv
}

function Get-ListeningProcess {
    param(
        [int]$Port,
        [string[]]$ExpectedNames
    )

    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($listener in $listeners) {
        $process = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
        if (-not $process) {
            continue
        }

        if ($ExpectedNames -contains $process.ProcessName) {
            return $process
        }
    }

    return $null
}

function Start-ManagedProcess {
    param(
        [string]$Name,
        [int]$Port,
        [string[]]$ExpectedProcessNames,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory,
        [string]$StdOutFile,
        [string]$StdErrFile
    )

    $existing = Get-ListeningProcess -Port $Port -ExpectedNames $ExpectedProcessNames
    if ($existing) {
        Write-Host "$Name already running (PID $($existing.Id))."
        return
    }

    $process = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -PassThru
    Write-Host "Started $Name (PID $($process.Id))."

    if ($StdOutFile) {
        Set-Content -Path $StdOutFile -Value "Started $Name wrapper process PID $($process.Id)" -Encoding ascii
    }
    if ($StdErrFile) {
        Set-Content -Path $StdErrFile -Value "" -Encoding ascii
    }
}

if (-not $SkipMongo) {
    if (-not (Test-Path $mongoExe)) {
        Write-Warning "MongoDB binary tidak ditemukan di: $mongoExe"
    } else {
        Start-ManagedProcess -Name "MongoDB" -Port 27017 -ExpectedProcessNames @("mongod") -FilePath $mongoExe -ArgumentList @(
            "--dbpath", $dataDb,
            "--bind_ip", "127.0.0.1",
            "--port", "27017",
            "--logpath", $mongoLog,
            "--logappend"
        ) -WorkingDirectory $repoRoot -StdOutFile "" -StdErrFile ""
    }
}

if (-not $SkipBackend) {
    $pythonExecutable = $null
    $pythonPrefixArgs = @()

    $python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if ($python) {
        $pythonExecutable = $python.Source
    }

    if (-not $pythonExecutable) {
        $python312 = Get-Command python3.12 -CommandType Application -ErrorAction SilentlyContinue
        if ($python312) {
            $pythonExecutable = $python312.Source
        }
    }

    if (-not $pythonExecutable) {
        $pyLauncher = Get-Command py -CommandType Application -ErrorAction SilentlyContinue
        if ($pyLauncher) {
            $pythonExecutable = $pyLauncher.Source
            $pythonPrefixArgs = @("-3.12")
        }
    }

    if (-not $pythonExecutable) {
        throw "Python executable tidak ditemukan. Install Python 3.12 lalu jalankan ulang script ini."
    }

    $backendArgs = $pythonPrefixArgs + @(
        "-m", "uvicorn",
        "server:app",
        "--app-dir", "backend",
        "--host", "0.0.0.0",
        "--port", "8000"
    )

    if ($BackendReload) {
        $backendArgs += "--reload"
    }

    Start-ManagedProcess -Name "Backend" -Port 8000 -ExpectedProcessNames @("python", "python3", "python3.12") -FilePath $pythonExecutable -ArgumentList $backendArgs -WorkingDirectory $repoRoot -StdOutFile "" -StdErrFile ""
}

if (-not $SkipFrontend) {
    $npm = Get-Command npm.cmd -CommandType Application -ErrorAction SilentlyContinue
    if (-not $npm) {
        throw "npm.cmd tidak ditemukan. Install Node.js lalu jalankan ulang script ini."
    }

    Start-ManagedProcess -Name "Frontend" -Port 3000 -ExpectedProcessNames @("node", "npm") -FilePath $npm.Source -ArgumentList @("--prefix", "frontend", "start") -WorkingDirectory $repoRoot -StdOutFile "" -StdErrFile ""
}

Write-Host ""
Write-Host "Service URLs:"
Write-Host "  Backend  : http://localhost:8000/api/"
Write-Host "  Frontend : http://localhost:3000"
Write-Host ""
Write-Host "Gunakan scripts/stop-dev.ps1 untuk mematikan service."