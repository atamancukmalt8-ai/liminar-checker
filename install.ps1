# LiminarChecker HTTPS bootstrapper.
# Publish this script and LiminarChecker.exe at a trusted HTTPS location, then
# replace EXE_URL before publishing. The SHA-256 pins the exact release below.

$ErrorActionPreference = 'Stop'

$ExeUrl = 'https://raw.githubusercontent.com/atamancukmalt8-ai/liminar-checker/main/LiminarChecker.exe'
$ExpectedSha256 = '366328E7932FF968AF9EE537D408BCCA7795349C4F56055086CD3FD7DBFDEA25'

if ($ExeUrl -notmatch '^https://') {
    throw 'Refusing to download from a non-HTTPS URL.'
}

$InstallDirectory = Join-Path $env:LOCALAPPDATA 'LiminarChecker'
$TargetPath = Join-Path $InstallDirectory 'LiminarChecker.exe'
$StagingPath = Join-Path $InstallDirectory 'LiminarChecker.download'

New-Item -ItemType Directory -Path $InstallDirectory -Force | Out-Null
Invoke-WebRequest -Uri $ExeUrl -OutFile $StagingPath

$ActualSha256 = (Get-FileHash -LiteralPath $StagingPath -Algorithm SHA256).Hash.ToUpperInvariant()
if ($ActualSha256 -ne $ExpectedSha256) {
    Remove-Item -LiteralPath $StagingPath -Force -ErrorAction SilentlyContinue
    throw "Downloaded file hash does not match the published LiminarChecker release. Got: $ActualSha256"
}

Move-Item -LiteralPath $StagingPath -Destination $TargetPath -Force
Write-Host 'LiminarChecker verified and ready.' -ForegroundColor Green
Start-Process -FilePath $TargetPath
