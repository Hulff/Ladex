# Tabular Text Converter

TabConv is an offline desktop app and command-line tool for previewing and cleaning CSV, TSV, and
plain-text tables. Imported values stay as strings, and importing or transforming data never edits
the source files.

## Install and run

Python 3.11 or newer is required.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
tabconv-gui
```

On Windows PowerShell, activate the environment with `.venv\\Scripts\\Activate.ps1`.

To inspect a file from the command line, run `tabconv path/to/file.csv`. The GUI opens from the
application menu or by running `tabconv-gui`.

## Desktop app

- Choose **English (US)** or **Português (Brasil)** in the Language selector.
- Open one or more CSV, TSV, or TXT files with **Open file(s)…**, or drag them into the window.
- Set the delimiter, text encoding, and whether the first row contains column names. Delimiter and
  encoding changes reload the selected files.
- Preview files in separate tabs. Files can have different columns and row counts.
- Use **Processed** and **Original** to switch the preview. Changed cells are highlighted in the
  processed view.
- Apply text replacement, decimal separator conversion, or column removal to the batch. When a
  column is selected, operations target that column name in every file where it appears.
- Use **Undo**, **Redo**, and **Reset changes** to manage the shared transformation history.
- **Export processed data…** exports the file shown in the current tab. **Export all files…** writes
  every processed file into a folder you choose, keeping each input file's CSV, TSV, or TXT format.
- The **Remove `_converted` from filenames** option controls whether exports get the default
  `_converted` filename suffix. Batch export checks for duplicate output names, protects imported
  source files, and asks before replacing existing output files.
- Single-file text export lets you choose delimiter, header inclusion, line ending, and encoding.
  XLSX is available for single-file export.
- Imports, transformations, and exports run outside the UI thread. A Cancel button appears while
  import or export work is running.

Rows with inconsistent field counts prompt you to pad short rows, truncate rows to the first row's
width, or cancel the import. The original files remain unchanged.

## Command-line usage

```sh
tabconv path/to/input.csv
```

The command-line interface reports the detected table structure and parsing issues. Use
`tabconv --help` to see available options.

## Development checks

```sh
pytest
pytest -m slow -s
ruff check .
mypy src/tabconv
```

The slow test parses 100,000 rows and reports elapsed time. The table view is virtualized, but the
parser retains imported datasets in memory, so very large inputs are limited by available memory.

## Build desktop packages

On Windows, install the development dependencies and run:

```powershell
py -m pip install -e '.[dev]'
.\\scripts\\build-windows.ps1
```

This creates `dist\\TabConv.exe`.

On Linux, install the project and PyInstaller, then run:

```sh
python -m pip install -e '.[dev]'
./scripts/build-linux.sh
```

This creates `dist/TabConv` and `dist/TabConv.AppDir`. If `appimagetool` is installed, the script
also creates an AppImage. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design details and
current limitations.
