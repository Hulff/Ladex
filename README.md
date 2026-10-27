# Tabular Text Converter

TabConv is an offline desktop app for previewing and cleaning CSV, TSV, and whitespace-delimited
text. It keeps imported values as strings and never changes the source during import or processing.

## Run and develop

Python 3.11 or newer is required.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
tabconv-gui
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and run `tabconv-gui`.
The CLI can inspect an input file with `tabconv example.txt`.

## Features

- Open or drop one or more CSV, TSV, and TXT files; select delimiter, encoding, and header behavior.
- Preview each file separately, even when files have different row counts or columns.
- Apply corrections to matching column names across the batch; deleting a name removes all columns
  with that name from every file. Export applies to the currently selected file.
- Resolve inconsistent rows by padding short rows, truncating to the first row's width, or cancelling.
- Replace literal text, convert decimal separators in numeric values, and remove columns.
- Preview original or processed data, see changed cells, and inspect/undo/redo/reset operations.
- Export to CSV, TSV, TXT, or XLSX. Text export supports delimiter, header, line ending, and encoding.
- Import, transforms, and exports run outside the UI thread; long imports and exports can be cancelled.
- Exports are written to a temporary file and only moved into place after success. Existing files,
  including the imported source, require an explicit confirmation in the UI.

## Tests and checks

```sh
pytest
pytest -m slow -s
ruff check .
mypy src/tabconv
```

The slow test parses 100,000 rows and reports elapsed time. The table view is virtualized, while
the current parser retains the full dataset in memory; very large files are therefore bounded by
available memory rather than streamed from disk.

## Windows build

On Windows, install the project and run:

```powershell
py -m pip install -e '.[dev]'
.\scripts\build-windows.ps1
```

This creates `dist\TabConv.exe`. The GitHub Actions workflow builds and smoke-tests it on Windows.

## Linux and AppImage build

On Linux, install the project and PyInstaller, then run:

```sh
python -m pip install -e '.[dev]'
./scripts/build-linux.sh
```

This creates `dist/TabConv` and `dist/TabConv.AppDir`. If `appimagetool` is installed or
`APPIMAGETOOL` points to it, the script also creates `dist/TabConv-x86_64.AppImage`. The Linux
workflow builds both artifacts on Ubuntu and uploads them.

## Arch Linux desktop entry

Install Python and the usual build tools (`python`, `python-pip`, and `base-devel`), create a
virtual environment, and install TabConv as above. To add the AppImage to the application menu,
make it executable and create `~/.local/share/applications/tabconv.desktop`:

```ini
[Desktop Entry]
Name=Tabular Text Converter
Exec=/absolute/path/to/TabConv-x86_64.AppImage
Icon=/absolute/path/to/tabconv.svg
Terminal=false
Type=Application
Categories=Office;Utility;
```

Use the icon at `packaging/tabconv.svg` or copy it to a stable location. Log out and back in, or
refresh the desktop application database, if the launcher does not appear immediately.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the core design and remaining limits.
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
