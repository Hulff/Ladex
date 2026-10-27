$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'Build this target on Windows. PyInstaller does not cross-compile Windows executables.'
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name TabConv `
    --icon icon/favicon.ico `
    --add-data "icon/favicon.ico;." `
    --paths src `
    --collect-all charset_normalizer `
    --collect-all openpyxl `
    --collect-all PySide6 `
    src/tabconv_gui_entry.py

Write-Host 'Created dist\TabConv.exe'
