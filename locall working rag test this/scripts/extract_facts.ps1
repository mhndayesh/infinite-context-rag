$files = Get-ChildItem -Path "c:\new-ai,arch\archive\512k_window_evaluation\dataset512k\*.txt" | Select-Object -First 10
$i = 1
foreach ($file in $files) {
    $text = Get-Content $file.FullName -TotalCount 50 -Encoding UTF8 | Out-String
    
    $matches = [regex]::Matches($text, "<p> (.*?) \.")
    if ($matches.Count -ge 2) {
        Write-Host "File: $($file.Name)"
        Write-Host "Fact: $($matches[1].Groups[1].Value)"
        Write-Host ""
        $i++
    }
}
