Add-Type -AssemblyName System.IO.Compression.FileSystem

$zipPath = 'C:\Users\techb\OneDrive\Desktop\cpl_hackathon\Crop_disease_prediction_online\cpl_crop_disease_model_bundle.zip'
$destRoot = 'C:\Users\techb\OneDrive\Desktop\cpl_hackathon\Crop_disease_prediction_online'

$destFull = [System.IO.Path]::GetFullPath($destRoot)
if (-not $destFull.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
    $destFull = $destFull + [System.IO.Path]::DirectorySeparatorChar
}

$zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
$extractedFiles = 0
$extractedDirs = 0
$skipped = @()

try {
    foreach ($entry in $zip.Entries) {
        # Reject absolute paths or anything containing parent-dir traversal
        if ($entry.FullName.Contains('..') -or [System.IO.Path]::IsPathRooted($entry.FullName)) {
            $skipped += $entry.FullName
            continue
        }

        $targetPath = Join-Path $destRoot $entry.FullName
        $targetFull = [System.IO.Path]::GetFullPath($targetPath)

        # Make sure resolved path is still inside destination
        if (-not $targetFull.StartsWith($destFull, [System.StringComparison]::OrdinalIgnoreCase)) {
            $skipped += $entry.FullName
            continue
        }

        if ($entry.FullName.EndsWith('/') -or $entry.FullName.EndsWith('\')) {
            # Directory entry
            if (-not (Test-Path -LiteralPath $targetFull)) {
                New-Item -ItemType Directory -Path $targetFull -Force | Out-Null
            }
            $extractedDirs++
        } else {
            $parentDir = [System.IO.Path]::GetDirectoryName($targetFull)
            if (-not (Test-Path -LiteralPath $parentDir)) {
                New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
            }
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $targetFull, $true)
            $extractedFiles++
        }
    }
}
finally {
    $zip.Dispose()
}

Write-Host ("Extracted files: {0}" -f $extractedFiles)
Write-Host ("Extracted dirs : {0}" -f $extractedDirs)
if ($skipped.Count -gt 0) {
    Write-Host "Skipped (unsafe paths):"
    $skipped | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "No unsafe paths."
}
