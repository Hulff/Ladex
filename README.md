# Tabular Text Converter

An offline desktop-oriented converter for CSV, TSV, and whitespace-delimited text. This
first milestone implements the GUI-independent import core and a small inspection CLI.

```sh
python -m pip install -e '.[dev]'
tabconv example.txt
pytest
ruff check .
mypy src/tabconv
```

## Windows executable

Build the executable on Windows (or let the included GitHub Actions workflow do it):

```powershell
py -m pip install -e '.[dev]'
.\scripts\build-windows.ps1
```

The result is `dist\TabConv.exe`. It is a self-contained executable for the current
CLI milestone; the future Qt desktop interface will use the same packaging target.
Windows executables cannot be reliably built on Linux with PyInstaller, so the CI job
uses `windows-latest` and uploads the generated artifact.

The parser keeps every value as text, recognizes quoted fields, and reports inconsistent
rows instead of dropping them. See `docs/ARCHITECTURE.md` for the staged implementation plan.
