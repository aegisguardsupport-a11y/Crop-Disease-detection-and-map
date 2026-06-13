# Live-server smoke test: starts uvicorn, hits /health /ready /docs /metrics
# /predict, then stops the server. Exits non-zero if any check fails.

$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\techb\OneDrive\Desktop\cpl_hackathon\Crop_disease_prediction_online'

$python = '.\.venv\Scripts\python.exe'
$port = 8765
$baseUrl = "http://127.0.0.1:$port"

# Start server in a background job so we can hit it from this script.
$job = Start-Job -ScriptBlock {
    param($cwd, $py, $port)
    Set-Location $cwd
    & $py -m uvicorn cpl_crop.api.app:create_app --factory --host 127.0.0.1 --port $port
} -ArgumentList $PWD.Path, $python, $port

Write-Host "Server starting (job id $($job.Id)). Waiting for readiness..."

$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "$baseUrl/ready" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        # not yet ready
    }
}

if (-not $ready) {
    Write-Host "Server did not become ready in 60s. Job output:"
    Receive-Job -Job $job
    Stop-Job -Job $job -ErrorAction SilentlyContinue
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    exit 1
}

$failures = 0

function Check {
    param($name, [scriptblock]$body)
    try {
        & $body
        Write-Host "  PASS  $name"
    } catch {
        Write-Host "  FAIL  $name : $_"
        $script:failures++
    }
}

Write-Host "Probing endpoints..."

Check '/health' {
    $r = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    if ($r.status -ne 'ok') { throw "expected status=ok, got $($r.status)" }
}

Check '/ready' {
    $r = Invoke-RestMethod -Uri "$baseUrl/ready" -Method Get
    if (-not $r.model_loaded) { throw "model_loaded=false" }
    if ($r.num_classes -ne 139) { throw "num_classes=$($r.num_classes)" }
}

Check '/docs' {
    $r = Invoke-WebRequest -Uri "$baseUrl/docs" -UseBasicParsing
    if ($r.StatusCode -ne 200) { throw "status=$($r.StatusCode)" }
    if ($r.Content -notmatch 'swagger') { throw 'no swagger marker in /docs' }
}

Check '/openapi.json' {
    $r = Invoke-RestMethod -Uri "$baseUrl/openapi.json"
    if (-not $r.paths.'/predict') { throw 'openapi missing /predict' }
}

Check '/metrics' {
    $r = Invoke-WebRequest -Uri "$baseUrl/metrics" -UseBasicParsing
    if ($r.StatusCode -ne 200) { throw "status=$($r.StatusCode)" }
    if ($r.Content -notmatch '# HELP') { throw 'not Prometheus format' }
}

Check '/predict' {
    Add-Type -AssemblyName System.Drawing
    $bmp = New-Object System.Drawing.Bitmap 300, 300
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::FromArgb(80, 140, 60))
    $g.Dispose()
    $tmp = [System.IO.Path]::GetTempFileName() + '.jpg'
    $bmp.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $bmp.Dispose()

    $r = & curl.exe --silent --show-error --fail `
        -F "file=@$tmp;type=image/jpeg" `
        -H 'X-Request-ID: live-smoke-1' `
        "$baseUrl/predict?topk=3"
    Remove-Item $tmp -ErrorAction SilentlyContinue

    $body = $r | ConvertFrom-Json
    if ($body.request_id -ne 'live-smoke-1') {
        throw "request_id mismatch: $($body.request_id)"
    }
    if ($body.predictions.Count -ne 3) {
        throw "predictions count $($body.predictions.Count)"
    }
    Write-Host "    top1: $($body.predictions[0].label) @ $([math]::Round($body.predictions[0].confidence*100,2))%  latency=$([math]::Round($body.latency_ms,1))ms"
}

Check '/explain' {
    Add-Type -AssemblyName System.Drawing
    $bmp = New-Object System.Drawing.Bitmap 300, 300
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::FromArgb(80, 140, 60))
    $g.Dispose()
    $tmp = [System.IO.Path]::GetTempFileName() + '.jpg'
    $bmp.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $bmp.Dispose()

    $r = & curl.exe --silent --show-error --fail `
        -F "file=@$tmp;type=image/jpeg" `
        -H 'X-Request-ID: explain-smoke-1' `
        "$baseUrl/explain?topk=3&num_samples=4&noise_level=0.10"
    Remove-Item $tmp -ErrorAction SilentlyContinue

    $body = $r | ConvertFrom-Json
    if ($body.request_id -ne 'explain-smoke-1') {
        throw "request_id mismatch: $($body.request_id)"
    }
    if (-not $body.heatmap_png_b64) { throw 'no heatmap_png_b64' }
    if (-not $body.overlay_png_b64) { throw 'no overlay_png_b64' }

    # Decode and write the overlay PNG so a human can inspect it.
    $outPath = Join-Path $PSScriptRoot 'last_overlay.png'
    [IO.File]::WriteAllBytes($outPath, [Convert]::FromBase64String($body.overlay_png_b64))
    Write-Host "    explained: $($body.explained_class_label)  method=$($body.method)  N=$($body.num_samples)  latency=$([math]::Round($body.latency_ms,0))ms"
    Write-Host "    overlay PNG written to $outPath ($((Get-Item $outPath).Length) bytes)"
}

Check '/predict-v2' {
    Add-Type -AssemblyName System.Drawing
    $bmp = New-Object System.Drawing.Bitmap 600, 600
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::FromArgb(80, 140, 60))
    # Add some texture so the quality check passes (random noise rectangles)
    $rng = New-Object System.Random 42
    for ($i = 0; $i -lt 600; $i += 12) {
        for ($j = 0; $j -lt 600; $j += 12) {
            $r = 60 + $rng.Next(0, 60)
            $gg = 100 + $rng.Next(0, 100)
            $b = 30 + $rng.Next(0, 60)
            $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb($r, $gg, $b))
            $g.FillRectangle($brush, $i, $j, 12, 12)
            $brush.Dispose()
        }
    }
    $g.Dispose()
    $tmp = [System.IO.Path]::GetTempFileName() + '.jpg'
    $bmp.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $bmp.Dispose()

    $r = & curl.exe --silent --show-error --fail `
        -F "file=@$tmp;type=image/jpeg" `
        -H 'X-Request-ID: v2-smoke-1' `
        "$baseUrl/predict-v2?topk=3&explain=true"
    Remove-Item $tmp -ErrorAction SilentlyContinue

    $body = $r | ConvertFrom-Json
    if ($body.request_id -ne 'v2-smoke-1') { throw "request_id mismatch" }
    if (-not $body.decision) { throw 'no decision field' }
    if (-not $body.validation.image_quality) { throw 'no image_quality' }
    if (-not $body.validation.leaf_segmentation) { throw 'no leaf_segmentation' }
    if (-not $body.confidence_signals) { throw 'no confidence_signals' }

    Write-Host "    decision: $($body.decision)  confidence: $([math]::Round($body.confidence*100,1))%  total: $([math]::Round($body.latency.total_ms,0))ms"
    Write-Host "    quality=$([math]::Round($body.validation.image_quality.score,2))  seg=$([math]::Round($body.validation.leaf_segmentation.confidence,2))  detected=$($body.validation.leaf_segmentation.detected)"
    if ($body.predictions.Count -gt 0) {
        Write-Host "    top1: $($body.predictions[0].label) @ $([math]::Round($body.predictions[0].confidence*100,1))%"
    } else {
        Write-Host "    no predictions; retake_reason=$($body.retake_reason)"
    }

    # Save the cleaned leaf and overlay so a human can inspect what the classifier saw
    if ($body.clean_leaf_png_b64) {
        $cleanPath = Join-Path $PSScriptRoot 'last_v2_clean_leaf.png'
        [IO.File]::WriteAllBytes($cleanPath, [Convert]::FromBase64String($body.clean_leaf_png_b64))
        Write-Host "    clean leaf written to $cleanPath"
    }
    if ($body.mask_overlay_png_b64) {
        $maskPath = Join-Path $PSScriptRoot 'last_v2_mask_overlay.png'
        [IO.File]::WriteAllBytes($maskPath, [Convert]::FromBase64String($body.mask_overlay_png_b64))
        Write-Host "    mask overlay written to $maskPath"
    }
}

Write-Host "Stopping server..."
Stop-Job -Job $job -ErrorAction SilentlyContinue
Remove-Job -Job $job -Force -ErrorAction SilentlyContinue

if ($failures -gt 0) {
    Write-Host "$failures check(s) failed"
    exit 1
}
Write-Host "All live checks passed."
exit 0
