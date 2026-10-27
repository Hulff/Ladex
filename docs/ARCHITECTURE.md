# Architecture and delivery plan

The application separates a pure-Python `core` from its PySide6 UI. `Dataset` is
immutable and contains string-only rows; parsing produces a dataset or a typed error.
Delimiter/encoding detection and quote-aware whitespace tokenization are independently
testable. A CLI uses the same API, so no data logic depends on Qt.

1. **M1 (current):** input/parsing core, CLI inspection, tests.
2. **M2:** serializable transformations and history.
3. **M3:** atomic CSV/TSV/TXT/XLSX export.
4. **M4:** PySide6 virtualized UI, worker-based loading, packaging and performance checks.

No input file is changed by parsing. Inconsistent rows carry their row number and require
an explicit future resolution policy (pad, truncate, or cancel).
