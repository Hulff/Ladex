import csv
from collections.abc import Callable
from pathlib import Path

from ..errors import (
    InconsistentRowsError,
    MalformedQuotesError,
    OperationCancelledError,
    UnsupportedFormatError,
)
from ..models import Dataset, ImportOptions
from .delimiter import detect_delimiter
from .encoding import decode_bytes
from .whitespace import tokenize_whitespace

DEFAULT_IMPORT_OPTIONS = ImportOptions()


def read_file(
    path: Path,
    options: ImportOptions = DEFAULT_IMPORT_OPTIONS,
    cancelled: Callable[[], bool] | None = None,
) -> Dataset:
    suffix = path.suffix.lower()
    if suffix not in {".txt", ".csv", ".tsv"}:
        raise UnsupportedFormatError(f"Unsupported input format: {suffix or '(none)'}")
    text, _ = decode_bytes(path.read_bytes(), options.encoding)
    return parse_text(text, options, path, cancelled)


def parse_text(
    text: str,
    options: ImportOptions = DEFAULT_IMPORT_OPTIONS,
    source: Path | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> Dataset:
    lines = text.splitlines()
    delimiter = options.delimiter or detect_delimiter(lines)
    try:
        if delimiter == "whitespace":
            parsed = []
            for number, line in enumerate(lines, 1):
                if cancelled and cancelled():
                    raise OperationCancelledError("Import cancelled")
                if line.strip():
                    parsed.append((number, tokenize_whitespace(line)))
        else:
            if len(delimiter) != 1:
                raise UnsupportedFormatError("Delimiter must be one character or 'whitespace'")
            parsed = []
            for number, row in enumerate(
                csv.reader(lines, delimiter=delimiter, strict=True), 1
            ):
                if cancelled and cancelled():
                    raise OperationCancelledError("Import cancelled")
                if row:
                    parsed.append((number, row))
    except csv.Error as error:
        raise MalformedQuotesError(str(error)) from error
    if not parsed:
        return Dataset((), (), source)
    first = parsed[0][1]
    width = len(first)
    issues = [(line, width, len(row)) for line, row in parsed[1:] if len(row) != width]
    if issues and options.inconsistent_rows == "error":
        raise InconsistentRowsError(issues)
    if options.inconsistent_rows not in {"error", "pad", "truncate"}:
        raise UnsupportedFormatError(
            f"Unknown inconsistent row policy: {options.inconsistent_rows}"
        )
    if options.inconsistent_rows == "pad":
        width = max(len(row) for _, row in parsed)
        if options.has_header and len(first) < width:
            first = first + [f"Column {index}" for index in range(len(first) + 1, width + 1)]
        normalized = [row + [""] * (width - len(row)) for _, row in parsed]
        if options.has_header:
            normalized[0] = first
    elif options.inconsistent_rows == "truncate":
        normalized = [row[:width] for _, row in parsed]
    else:
        normalized = [row for _, row in parsed]
    if options.has_header:
        return Dataset(tuple(normalized[0]), tuple(tuple(row) for row in normalized[1:]), source)
    columns = tuple(f"Column {index}" for index in range(1, width + 1))
    return Dataset(columns, tuple(tuple(row) for row in normalized), source)
