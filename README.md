# Tabular Text Converter

An offline desktop-oriented converter for CSV, TSV, and whitespace-delimited text. It
includes a desktop import and preview interface, backed by a GUI-independent import core.

```sh
python -m pip install -e '.[dev]'
tabconv example.txt
tabconv-gui
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

The result is `dist\TabConv.exe`. It opens the desktop import and preview interface.
Windows executables cannot be reliably built on Linux with PyInstaller, so the CI job
uses `windows-latest` and uploads the generated artifact.

The parser keeps every value as text, recognizes quoted fields, and reports inconsistent
rows instead of dropping them. See `docs/ARCHITECTURE.md` for the staged implementation plan.
 # Tabular Text Converter

 An offline desktop-oriented converter for CSV, TSV, and whitespace-delimited text. It
 includes a desktop import and preview interface, backed by a GUI-independent import core.

 ```sh
 python -m pip install -e '.[dev]'
 tabconv example.txt
 tabconv-gui
 pytest
 ruff check .
 mypy src/tabconv
 ```

 ## Windows executable

 On Windows:

 ```powershell
 py -m pip install -e '.[dev]'
 .\scripts\build-windows.ps1
 ```

 The result is `dist\TabConv.exe`. It opens the desktop import and preview interface.
 Windows executables cannot be reliably built on Linux with PyInstaller, so the CI job
 uses `windows-latest` and uploads the generated artifact.
