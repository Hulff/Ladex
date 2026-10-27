# Architecture and delivery plan

The application separates a pure-Python `core` from its PySide6 UI. `Dataset` is
immutable and contains string-only rows; parsing produces a dataset or a typed error.
Delimiter/encoding detection and quote-aware whitespace tokenization are independently
testable. A CLI uses the same API, so no data logic depends on Qt.

1. **M1 (complete):** input/parsing core, CLI inspection, tests.
2. **M2 (complete):** serializable transformations and history.
3. **M3 (complete):** atomic CSV/TSV/TXT/XLSX export.
4. **M4 (implemented; local Linux verification complete):** PySide6 UI, worker-based loading,
   transformations and export, Windows and Linux packaging workflows, and checks. The Linux
   executable and AppDir pass a smoke launch. The AppImage and Windows executable are built by
   their native CI jobs and were not built in this environment.
5. **M5 (in progress):** open multiple datasets together, preview each file separately, and apply
   shared column-name transformations with one undo/redo history. Exports currently target the
   selected file.

No input file is changed by parsing. Inconsistent rows carry their row number and require
the UI offers padding, truncation, or cancellation. The parser retains complete datasets in
memory, although import and export work happens in background threads and the table view is
virtualized. Very large files are bounded by available memory rather than streamed from disk.
