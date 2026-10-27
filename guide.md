# Project: Tabular Text Converter (Python, desktop, offline)

## Objective
Build a complete, reliable, cross-platform desktop application (Windows and Linux, including Arch) for importing, cleaning, transforming, and exporting tabular text data. It must work 100% offline, with no account, no cloud, and no server.

## Required stack
- Python 3.11 or higher
- GUI: PySide6 (Qt), using `QTableView` + `QAbstractTableModel` (virtualized rendering)
- Parsing: stdlib `csv` module + a custom tokenizer for whitespace-delimited text
- Encoding detection: `charset-normalizer`
- XLSX export: `openpyxl` (`write_only` mode for large files)
- Tests: `pytest` (+ `pytest-qt` for basic UI tests)
- Quality: `ruff` and `mypy`
- Packaging: PyInstaller (Windows and Linux) and, if feasible, AppImage on Linux
- Dependency management: `uv` or `pip` with `pyproject.toml`

The data logic MUST NOT depend on Qt. It must run via CLI and in tests without a GUI.

## 1. Input
Formats: `.txt`, `.csv`, `.tsv`. Support UTF-8 (with and without BOM) and detect other encodings, with a manual override option.

Must handle: quoted headers, quoted fields containing spaces, tabs, configurable delimiter, repeated spaces as a delimiter, CRLF and LF, empty fields, empty lines, files without headers, and large files without freezing the UI.

Example input:

```
"collum 1" "col2"
11.214     1245,3
12.415     2256,7
```

Expected table: columns `collum 1` and `col2`; rows `11.214 | 1245,3` and `12.415 | 2256,7`.

Rules:
- Never use `split(' ')`. For whitespace-delimited text, implement a tokenizer that recognizes quotes and treats consecutive spaces/tabs outside quotes as a single delimiter.
- For CSV/TSV, use `csv` with proper quote and escape handling.
- If delimiter detection is ambiguous, ask the user instead of corrupting data.
- Rows with an inconsistent number of columns are never silently discarded: they are reported, and the user chooses to pad, truncate, or cancel.
- Values are always `str`. Never convert numbers automatically.
- Never overwrite the original file.

## 2. Import workflow
"Open file" button, drag and drop, extension filter, a preview before full processing, detected delimiter with manual override, a "first row is header" option, and encoding selection.

## 3. Preview
- Table with headers and row numbers, horizontal and vertical scrolling
- Row and column counts
- Column selection
- Modified cells/columns visually highlighted
- Toggle between "Original" and "Processed"
- Display of parsing errors
- Responsive UI with 100k rows (load incrementally or in a worker thread, never on the UI thread)

## 4. Transformations
Each transformation is an immutable, deterministic, serializable operation (dataclass), applied by the engine to the dataset.

**A. Replace literal text.** Parameters: text to find, replacement, columns (all or selected), case-sensitive. No regex by default.

**B. Convert decimal separator.** Directions: point→comma and comma→point. Scope: all columns or selected columns. Default mode: **numeric values only** (safe). Configure thousands convention (none, period, comma, space).
- `11.214` → `11,214`
- `1245,3` stays `1245,3` when converting point→comma
- Do not alter identifiers, dates, filenames, or text
- Never assume whether `1.234` is a decimal or a thousands separator: require explicit configuration when ambiguous

**C. Remove columns.** Panel with a list of columns and checkboxes, select/deselect all, confirmation before applying, and a clear "remove" vs "keep" indication. Does not mutate the original data.

**D. Extras (only after the core works):** trim, remove empty rows, remove duplicates, rename and reorder columns, fill empty cells.

The engine must allow new operations to be added via a simple registry (`Operation` base class + registry).

## 5. History
Clearly separate: original data (never changes), current data, and the list of operations. The current state is the result of reapplying the operations to the original. Undo, redo, reset all, and list applied operations. Reset restores the imported data.

## 6. Export
Formats: `.xlsx`, `.csv`, `.tsv`, `.txt`.
- Text: delimiter, include header or not, line ending (LF/CRLF), quoting/escape rules, encoding (default UTF-8)
- XLSX: values as strings by default, preserve column names and row order, no index column, the file must open in Excel and LibreOffice
- "Save as" dialog with a filename suggested from the input file
- Write to a temporary file and move it to the destination only on success (no partial files)
- Report success or a useful error
- Never overwrite the original without an explicit user decision

## 7. Interface
- Header: open, export, undo, redo
- Sidebar: import settings, operations, column management
- Main area: table with Original/Processed toggle
- Footer: current file, delimiter, number of transformations, export status
- Light/dark theme, shortcuts (Ctrl+O, Ctrl+Z, Ctrl+Y, Ctrl+S/E), clear empty states, progress bar for long operations, actionable error messages
- Avoid unnecessary animations and dialogs

## 8. Architecture
```
src/tabconv/
  core/
    models.py          # Dataset, Column, ImportOptions, ExportOptions, ProcessingResult
    errors.py          # typed errors
    parsing/
      encoding.py
      delimiter.py
      whitespace.py    # quote-aware tokenizer
      reader.py
    transforms/
      base.py
      replace.py
      decimal.py
      columns.py
      registry.py
    history.py
    export/
      text.py
      xlsx.py
  ui/                  # PySide6: main_window, table_model, sidebar, dialogs, workers
  cli.py               # tabconv input.txt --replace . , --drop 2 -o out.xlsx
  __main__.py
tests/
```
Typed errors: unsupported format, invalid encoding, malformed quotes, inconsistent rows, invalid transformation options, export failure. No monolithic files.

## 9. Safety and performance
Do not send data externally, do not execute file content, do not silently discard malformed rows, do not mutate the original, avoid unnecessary memory copies, virtualized table, heavy processing in `QThread`/worker. Initial target: 100k rows. Measure, document limitations, and only then optimize.

## 10. Tests (pytest)
1. Quoted header
2. Multiple spaces and tabs
3. Quoted values with spaces
4. CRLF and LF
5. File without header
6. Replace `.` in all columns
7. Replace `.` in selected columns only
8. Numeric-only decimal conversion
9. Preserve text identifiers
10. Remove columns
11. Undo/redo
12. Export and reimport CSV and TSV
13. Export XLSX and verify contents with `openpyxl`
14. Empty file and empty cells
15. Malformed input
16. Export failure (no partial file)
17. Large dataset (100k rows) with measured time

Use the exact example data from section 1 in the tests.

## 11. Build and distribution
Document in the README: installing dependencies, running in dev, tests, lint, PyInstaller builds for Windows and Linux, per-platform prerequisites, and Arch Linux instructions (required packages and creating a `.desktop` file to launch from the app launcher). Produce an AppImage on Linux when feasible. Do not claim the Windows build was tested if it was only built on Linux (use GitHub Actions CI with `windows-latest` or document it as unverified).

## 12. Workflow
1. Inspect the repository before changing anything.
2. If it is empty, scaffold the project (`pyproject.toml`, structure above).
3. Document the architecture and plan in `docs/ARCHITECTURE.md`.
4. Implement the core (parser, delimiter, encoding) with tests.
5. Implement transformations, history, and export with tests.
6. Only then build the GUI on top of the core.
7. Packaging and documentation.
8. Run tests, fix failures, verify the build.
9. Summarize what was done, the commands used, and any limitations.

Work incrementally: do not deliver just a plan or mockup.

## Milestones
- **M1:** import and parsing core + passing tests (via CLI, no GUI)
- **M2:** transformations, undo/redo, and column removal + tests
- **M3:** XLSX/CSV/TSV/TXT export + tests
- **M4:** GUI, performance with 100k rows, packaging, and documentation

Do not advance to the next milestone with failing tests.

## Definition of done
The user opens a text file, sees the parsed columns, swaps decimal separators, removes columns, previews the result, undoes operations, and exports to XLSX/CSV/TSV/TXT, repeating the workflow without ever altering the source file, all offline on Windows and Linux.