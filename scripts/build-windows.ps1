$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'Build this target on Windows. PyInstaller does not cross-compile Windows executables.'
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name TabConv `
    --paths src `
    --collect-all charset_normalizer `
    src/tabconv_entry.py

Write-Host 'Created dist\TabConv.exe'
