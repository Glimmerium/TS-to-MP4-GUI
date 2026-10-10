param([string]$Python = 'python')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    # Resolve before invoking anything, so a relative venv path is supported.
    $pythonCommand = (Get-Command $Python -ErrorAction Stop).Source
    $bundle = Join-Path $projectRoot 'dist\TS-MP4'
    & $pythonCommand scripts/prepare_runtime.py $bundle
    if ($LASTEXITCODE -ne 0) { throw 'A working 64-bit Windows Python with Tcl/Tk is required.' }

    & $pythonCommand -m PyInstaller --noconfirm --clean --onefile --windowed --name TS-MP4 --icon converter.ico --add-data "personal-logo.png;." converter.py
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }

    New-Item -ItemType Directory -Path $bundle -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $projectRoot 'dist\TS-MP4.exe') -Destination $bundle -Force
    foreach ($name in @('converter.ico', 'personal-logo.png', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md')) {
        Copy-Item -LiteralPath (Join-Path $projectRoot $name) -Destination $bundle -Force
    }
    # Explicit file list: do not accidentally ship locally copied engines/media.
    $packageFiles = @('TS-MP4.exe', 'converter.ico', 'personal-logo.png', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'licenses') |
        ForEach-Object { Join-Path $bundle $_ }
    $archive = Join-Path $projectRoot 'dist\TS-MP4-windows-x64.zip'
    Compress-Archive -LiteralPath $packageFiles -DestinationPath $archive -Force
    Write-Output "Built: $archive"
    Write-Output 'FFmpeg is not bundled. Follow README.md to prepare ffmpeg.exe and ffprobe.exe.'
} finally {
    Pop-Location
}
