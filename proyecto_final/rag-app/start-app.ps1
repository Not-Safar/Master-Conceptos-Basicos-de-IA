$ErrorActionPreference = 'Stop'
$projectDirectory = $PSScriptRoot
$pythonExecutable = Join-Path $projectDirectory '.venv\Scripts\python.exe'
$logDirectory = Join-Path $projectDirectory 'logs'

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw 'Falta .venv. Sigue los pasos de instalacion en README.md.'
}
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

function Start-LocalService {
    param([string]$Name, [int]$Port, [string]$HealthUrl, [string]$Arguments)
    try {
        $existingResponse = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 2
        if ($existingResponse.StatusCode -eq 200) {
            Write-Host "$Name ya esta disponible en el puerto $Port."
            return
        }
    } catch {
        # Si no responde, comprobar el puerto antes de iniciar otro proceso.
    }
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listener) {
        throw "El puerto $Port esta ocupado, pero $Name no responde. Revisa el proceso antes de reiniciarlo."
    }
    $serviceProcess = Start-Process -FilePath $pythonExecutable -ArgumentList $Arguments `
        -WorkingDirectory $projectDirectory -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logDirectory "$Name.out.log") `
        -RedirectStandardError (Join-Path $logDirectory "$Name.err.log")
    $serviceProcess.Id | Set-Content -LiteralPath (Join-Path $logDirectory "$Name.pid")
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        $serviceProcess.Refresh()
        if ($serviceProcess.HasExited) {
            throw "$Name termino durante el arranque. Revisa logs/$Name.err.log."
        }
        try {
            $readyResponse = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 2
            if ($readyResponse.StatusCode -eq 200) {
                Write-Host "$Name iniciado en el puerto $Port (PID $($serviceProcess.Id))."
                return
            }
        } catch {
            # Esperar a que termine el arranque del servicio.
        }
        Start-Sleep -Milliseconds 500
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "$Name no respondio en 30 segundos. Revisa logs/$Name.err.log."
}

Start-LocalService -Name 'api' -Port 8000 -HealthUrl 'http://127.0.0.1:8000/health' `
    -Arguments '-m uvicorn app.main:app --host 127.0.0.1 --port 8000'
Start-LocalService -Name 'ui' -Port 8501 -HealthUrl 'http://127.0.0.1:8501/_stcore/health' `
    -Arguments '-m streamlit run ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false'
Write-Host 'Aplicacion disponible: http://127.0.0.1:8501'
