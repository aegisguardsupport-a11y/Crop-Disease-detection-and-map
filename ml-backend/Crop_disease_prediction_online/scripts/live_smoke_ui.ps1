# Live combined smoke: start FastAPI + Streamlit in background jobs, probe both,
# stop them. Designed to be re-runnable.

$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\techb\OneDrive\Desktop\cpl_hackathon\Crop_disease_prediction_online'

$python = '.\.venv\Scripts\python.exe'
$apiPort = 8765
$uiPort = 8766

# --- API ---------------------------------------------------------------
$apiJob = Start-Job -ScriptBlock {
    param($cwd, $py, $port)
    Set-Location $cwd
    & $py -m uvicorn cpl_crop.api.app:create_app --factory --host 127.0.0.1 --port $port
} -ArgumentList $PWD.Path, $python, $apiPort
Write-Host "API job id $($apiJob.Id) starting on :$apiPort"

# Wait for /ready
$apiReady = $false
for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$apiPort/ready" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $apiReady = $true; break }
    } catch {}
}
if (-not $apiReady) {
    Write-Host "API didn't start in 90s. Output:"
    Receive-Job -Job $apiJob
    Stop-Job -Job $apiJob -ErrorAction SilentlyContinue
    Remove-Job -Job $apiJob -Force -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "API ready."

# --- Streamlit ---------------------------------------------------------
$uiJob = Start-Job -ScriptBlock {
    param($cwd, $py, $port)
    Set-Location $cwd
    & $py -m streamlit run streamlit_app\streamlit_app.py `
        --server.port $port `
        --server.headless true `
        --browser.gatherUsageStats false
} -ArgumentList $PWD.Path, $python, $uiPort
Write-Host "Streamlit job id $($uiJob.Id) starting on :$uiPort"

$uiReady = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$uiPort/" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $uiReady = $true; break }
    } catch {}
}
if (-not $uiReady) {
    Write-Host "Streamlit didn't start in 60s. Output:"
    Receive-Job -Job $uiJob
    Stop-Job -Job $uiJob, $apiJob -ErrorAction SilentlyContinue
    Remove-Job -Job $uiJob, $apiJob -Force -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "Streamlit responding on :$uiPort"

# Verify Streamlit returns the app HTML
$resp = Invoke-WebRequest -Uri "http://127.0.0.1:$uiPort/" -UseBasicParsing
if ($resp.Content -match 'streamlit') {
    Write-Host "  Streamlit HTML contains 'streamlit' marker — OK"
} else {
    Write-Host "  WARN — Streamlit HTML doesn't look right (first 200 chars):"
    Write-Host "  $($resp.Content.Substring(0, [Math]::Min(200, $resp.Content.Length)))"
}

# --- Stop everything ---------------------------------------------------
Write-Host "Stopping jobs..."
Stop-Job -Job $apiJob, $uiJob -ErrorAction SilentlyContinue
Remove-Job -Job $apiJob, $uiJob -Force -ErrorAction SilentlyContinue
Write-Host "Live smoke OK."
