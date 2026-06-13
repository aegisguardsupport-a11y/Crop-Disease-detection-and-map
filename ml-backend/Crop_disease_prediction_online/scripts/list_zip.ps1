Add-Type -AssemblyName System.IO.Compression.FileSystem
$zipPath = 'C:\Users\techb\OneDrive\Desktop\cpl_hackathon\Crop_disease_prediction_online\cpl_crop_disease_model_bundle.zip'
$zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
$zip.Entries | Sort-Object FullName | ForEach-Object {
    $sizeMB = [math]::Round($_.Length / 1MB, 3)
    "{0,10} MB  {1}" -f $sizeMB, $_.FullName
}
Write-Host "---"
Write-Host ("Total entries: {0}" -f $zip.Entries.Count)
$zip.Dispose()
