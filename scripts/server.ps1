<#
.SYNOPSIS
    Manages the Django development server lifecycle for AI Agent environments.

.DESCRIPTION
    Controls start/stop/restart/status of the Django dev server.
    Designed for OpenCode/AI Agent shells where spawned processes must not block.
    Uses Start-Process -WindowStyle Hidden to fully detach the server process.

.PARAMETER Command
    The action to perform: start, stop, restart, or status.

.PARAMETER Port
    The port for the Django server (default: 8000).

.PARAMETER Settings
    Django settings module (default: config.settings.dev).

.PARAMETER ListenAddress
    The host to bind to (default: 0.0.0.0). NOTE: Named -ListenAddress
    because -Host conflicts with PowerShell's read-only $Host variable.
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Command,

    [int]$Port = 8001,

    [string]$Settings = "config.settings.demo",

    [string]$ListenAddress = "127.0.0.1"
)

# NOTE: -Host is unavailable as a parameter name because $Host is a
# read-only automatic variable in PowerShell 5.1. Use -ListenAddress instead.

$ProjectRoot = "D:\Jarvis project"
$PidFile = Join-Path -Path $ProjectRoot -ChildPath ".server.pid"
$LogDir = Join-Path -Path $ProjectRoot -ChildPath "logs"
$StdoutLog = Join-Path -Path $LogDir -ChildPath "server_stdout.log"
$StderrLog = Join-Path -Path $LogDir -ChildPath "server_stderr.log"
$PythonExe = Join-Path -Path $ProjectRoot -ChildPath ".venv\Scripts\python.exe"

function Ensure-LogDir {
    if (-not (Test-Path -LiteralPath $LogDir)) {
        $null = New-Item -ItemType Directory -Path $LogDir -Force
    }
}

function Get-SavedPid {
    if (Test-Path -LiteralPath $PidFile) {
        $content = Get-Content -Path $PidFile -Raw -ErrorAction SilentlyContinue
        if ($content -match '\d+') {
            $pidVal = [int]$Matches[0]
            $proc = Get-Process -Id $pidVal -ErrorAction SilentlyContinue
            if ($proc) {
                return $pidVal
            }
        }
    }
    return $null
}

function Test-PortListening {
    param([int]$PortNumber)
    $lines = netstat -ano | Select-String ":$PortNumber\s"
    foreach ($line in $lines) {
        if ($line.Line -match 'LISTENING') {
            return $true
        }
    }
    return $false
}

function Get-ListeningPids {
    param([int]$PortNumber)
    $pids = @()
    $lines = netstat -ano | Select-String ":$PortNumber\s"
    foreach ($line in $lines) {
        if ($line.Line -match 'LISTENING' -and $line.Line -match '\s+(\d+)\s*$') {
            $matchPid = [int]$Matches[1]
            if ($matchPid -gt 0 -and $pids -notcontains $matchPid) {
                $pids += $matchPid
            }
        }
    }
    return $pids
}

function Test-Http {
    param([string]$TargetHost, [int]$TargetPort)
    try {
        $response = Invoke-WebRequest -Uri "http://${TargetHost}:${TargetPort}/" -TimeoutSec 3 -UseBasicParsing
        return $response.StatusCode
    } catch {
        if ($_.Exception.Response) {
            try {
                return [int]$_.Exception.Response.StatusCode
            } catch {
                return $null
            }
        }
        return $null
    }
}

switch ($Command) {
    "start" {
        $existingPid = Get-SavedPid
        if ($existingPid) {
            Write-Host "Server already running (PID: $existingPid)"
            exit 0
        }

        if (Test-PortListening -PortNumber $Port) {
            Write-Host "Port ${Port} in use by unknown process. Use stop first"
            exit 1
        }

        Ensure-LogDir

        if (-not (Test-Path -LiteralPath $PythonExe)) {
            Write-Host "ERROR: Python not found at $PythonExe. Run 'python -m venv .venv' first"
            exit 1
        }
        $managePy = Join-Path -Path $ProjectRoot -ChildPath "manage.py"
        if (-not (Test-Path -LiteralPath $managePy)) {
            Write-Host "ERROR: manage.py not found at $managePy"
            exit 1
        }

        $proc = Start-Process -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput $StdoutLog `
            -RedirectStandardError $StderrLog `
            -FilePath $PythonExe `
            -ArgumentList "-m", "daphne", "-b", $ListenAddress, "-p", $Port, "config.asgi:application" `
            -WorkingDirectory $ProjectRoot

        $serverPid = $proc.Id
        Set-Content -Path $PidFile -Value $serverPid

        $timeout = 15000
        $interval = 500
        $elapsed = 0
        $portDetected = $false

        while ($elapsed -lt $timeout) {
            Start-Sleep -Milliseconds $interval
            $elapsed += $interval

            if (Test-PortListening -PortNumber $Port) {
                $portDetected = $true
                break
            }

            $procAlive = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
            if (-not $procAlive) {
                Write-Host "ERROR: Server process (PID: $serverPid) exited unexpectedly"
                exit 1
            }
        }

        if ($portDetected) {
            $httpResult = Test-Http -TargetHost "localhost" -TargetPort $Port
            if ($httpResult) {
                Write-Host "Server started. PID: $serverPid. HTTP status: $httpResult"
            } else {
                Write-Host "Server started (port open, no HTTP response yet)"
            }
        } else {
            Write-Host "WARNING: Server process started but port not detected within 15s"
            exit 1
        }

        exit 0
    }

    "stop" {
        $killedPid = $null
        $startTime = Get-Date

        if (Test-Path -LiteralPath $PidFile) {
            $content = Get-Content -Path $PidFile -Raw -ErrorAction SilentlyContinue
            if ($content -match '\d+') {
                $killedPid = [int]$Matches[0]
                taskkill /PID $killedPid /T /F 2>$null
            }
        }

        if (-not $killedPid) {
            $portPids = Get-ListeningPids -PortNumber $Port
            foreach ($p in $portPids) {
                taskkill /PID $p /T /F 2>$null
                if (-not $killedPid) {
                    $killedPid = $p
                }
            }
        }

        $timeout = 8000
        $interval = 300
        $elapsed = 0
        $portReleased = $false

        while ($elapsed -lt $timeout) {
            Start-Sleep -Milliseconds $interval
            $elapsed += $interval
            if (-not (Test-PortListening -PortNumber $Port)) {
                $portReleased = $true
                break
            }
        }

        $duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)

        if ($killedPid -or $portReleased) {
            Write-Host "Server stopped. PID: $killedPid. Port released in ${duration}s"
        } else {
            Write-Host "No server was running"
        }

        if (Test-Path -LiteralPath $PidFile) {
            Remove-Item -Path $PidFile -Force
        }

        exit 0
    }

    "restart" {
        Write-Host "Restarting server..."

        # --- Stop phase ---
        $killedPid = $null

        if (Test-Path -LiteralPath $PidFile) {
            $content = Get-Content -Path $PidFile -Raw -ErrorAction SilentlyContinue
            if ($content -match '\d+') {
                $killedPid = [int]$Matches[0]
                taskkill /PID $killedPid /T /F 2>$null
            }
        }

        if (-not $killedPid) {
            $portPids = Get-ListeningPids -PortNumber $Port
            foreach ($p in $portPids) {
                taskkill /PID $p /T /F 2>$null
                if (-not $killedPid) {
                    $killedPid = $p
                }
            }
        }

        $stopTimeout = 8000
        $stopElapsed = 0
        while ($stopElapsed -lt $stopTimeout) {
            Start-Sleep -Milliseconds 300
            $stopElapsed += 300
            if (-not (Test-PortListening -PortNumber $Port)) {
                break
            }
        }

        if (Test-Path -LiteralPath $PidFile) {
            Remove-Item -Path $PidFile -Force
        }

        # --- Start phase ---
        Ensure-LogDir

        if (-not (Test-Path -LiteralPath $PythonExe)) {
            Write-Host "ERROR: Python not found at $PythonExe. Run 'python -m venv .venv' first"
            exit 1
        }
        $managePy = Join-Path -Path $ProjectRoot -ChildPath "manage.py"
        if (-not (Test-Path -LiteralPath $managePy)) {
            Write-Host "ERROR: manage.py not found at $managePy"
            exit 1
        }

        $proc = Start-Process -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput $StdoutLog `
            -RedirectStandardError $StderrLog `
            -FilePath $PythonExe `
            -ArgumentList "-m", "daphne", "-b", $ListenAddress, "-p", $Port, "config.asgi:application" `
            -WorkingDirectory $ProjectRoot

        $serverPid = $proc.Id
        Set-Content -Path $PidFile -Value $serverPid

        $startTimeout = 15000
        $startElapsed = 0
        $portDetected = $false

        while ($startElapsed -lt $startTimeout) {
            Start-Sleep -Milliseconds 500
            $startElapsed += 500
            if (Test-PortListening -PortNumber $Port) {
                $portDetected = $true
                break
            }
            $procAlive = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
            if (-not $procAlive) {
                break
            }
        }

        if ($portDetected) {
            $httpResult = Test-Http -TargetHost "localhost" -TargetPort $Port
            if ($httpResult) {
                Write-Host "Server started. PID: $serverPid. HTTP status: $httpResult"
            } else {
                Write-Host "Server started (port open, no HTTP response yet)"
            }
        } else {
            Write-Host "WARNING: Server process started but port not detected within 15s"
            exit 1
        }

        Write-Host "Restart complete"
        exit 0
    }

    "status" {
        $savedPid = Get-SavedPid
        $listening = Test-PortListening -PortNumber $Port

        if ($savedPid) {
            Write-Host "Status: running"
            Write-Host "PID: $savedPid"
            Write-Host "Port: $Port"
            Write-Host "Listening: ${listening}"
            $httpCode = Test-Http -TargetHost "localhost" -TargetPort $Port
            if ($httpCode) {
                Write-Host "HTTP check: $httpCode"
            }
        } else {
            Write-Host "Status: stopped"
            Write-Host "PID: none"
            Write-Host "Port: $Port"
            Write-Host "Listening: false"
        }

        exit 0
    }
}
