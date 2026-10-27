import csv
from pathlib import Path

from ..errors import InconsistentRowsError, MalformedQuotesError, UnsupportedFormatError
from ..models import Dataset, ImportOptions
from .delimiter import detect_delimiter
from .encoding import decode_bytes
from .whitespace import tokenize_whitespace


def read_file(path: Path, options: ImportOptions = ImportOptions()) -> Dataset:
    suffix = path.suffix.lower()
    if suffix not in {".txt", ".csv", ".tsv"}:
        raise UnsupportedFormatError(f"Unsupported input format: {suffix or '(none)'}")
    text, _ = decode_bytes(path.read_bytes(), options.encoding)
    return parse_text(text, options, path)


def parse_text(text: str, options: ImportOptions = ImportOptions(), source: Path | None = None) -> Dataset:
    lines = text.splitlines()
    delimiter = options.delimiter or detect_delimiter(lines)
    try:
        if delimiter == "whitespace":
            parsed = [(number, tokenize_whitespace(line)) for number, line in enumerate(lines, 1) if line.strip()]
        else:
            if len(delimiter) != 1:
                raise UnsupportedFormatError("Delimiter must be one character or 'whitespace'")
            parsed = [
                (number, row)
                for number, row in enumerate(csv.reader(lines, delimiter=delimiter, strict=True), 1)
                if row
            ]
    except csv.Error as error:
        raise MalformedQuotesError(str(error)) from error
    if not parsed:
        return Dataset((), (), source)
    first = parsed[0][1]
    width = len(first)
    issues = [(line, width, len(row)) for line, row in parsed[1:] if len(row) != width]
    if issues:
        raise InconsistentRowsError(issues)
    if options.has_header:
        return Dataset(tuple(first), tuple(tuple(row) for _, row in parsed[1:]), source)
    columns = tuple(f"Column {index}" for index in range(1, width + 1))
    return Dataset(columns, tuple(tuple(row) for _, row in parsed), source)
