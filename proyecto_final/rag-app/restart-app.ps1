$ErrorActionPreference = 'Stop'
$expectedPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$serviceDefinitions = @(
    @{ Name = 'api'; Pattern = '-m\s+uvicorn\s+app\.main:app\b' },
    @{ Name = 'ui'; Pattern = '-m\s+streamlit\s+run\s+ui[\\/]streamlit_app\.py\b' }
)
$verifiedProcesses = @()

# Verificar todos los PID antes de detener nada; un PID antiguo puede reutilizarse.
foreach ($definition in $serviceDefinitions) {
    $pidFile = Join-Path $PSScriptRoot "logs/$($definition.Name).pid"
    if (-not (Test-Path -LiteralPath $pidFile)) { continue }
    $serviceProcessId = [int](Get-Content -LiteralPath $pidFile -Raw).Trim()
    $serviceProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $serviceProcessId"
    if (-not $serviceProcess) { continue }
    if ($serviceProcess.ExecutablePath -ne $expectedPython -or
        $serviceProcess.CommandLine -notmatch $definition.Pattern) {
        throw "El PID registrado para $($definition.Name) pertenece a otro proceso. No se detuvo."
    }
    $verifiedProcesses += @{ Name = $definition.Name; ProcessId = $serviceProcessId }
}

foreach ($service in $verifiedProcesses) {
    # El Python del venv crea un proceso hijo; detener tambien su arbol.
    & taskkill.exe /PID $service.ProcessId /T /F | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo detener $($service.Name)."
    }
    Write-Host "$($service.Name) detenido."
}

& (Join-Path $PSScriptRoot 'start-app.ps1')
