import codecs
import csv
from collections.abc import Callable, Iterable
from pathlib import Path

from ..errors import (
    InconsistentRowsError,
    InvalidEncodingError,
    MalformedQuotesError,
    OperationCancelledError,
    UnsupportedFormatError,
)
from ..models import Dataset, ImportOptions
from .delimiter import detect_delimiter
from .whitespace import tokenize_whitespace

DEFAULT_IMPORT_OPTIONS = ImportOptions()
_SAMPLE_BYTES = 64 * 1024


def read_file(
    path: Path,
    options: ImportOptions = DEFAULT_IMPORT_OPTIONS,
    cancelled: Callable[[], bool] | None = None,
    progress: Callable[[int], None] | None = None,
) -> Dataset:
    suffix = path.suffix.lower()
    if suffix not in {".txt", ".csv", ".tsv"}:
        raise UnsupportedFormatError(f"Unsupported input format: {suffix or '(none)'}")
    encoding = _detect_encoding(path, options.encoding)
    try:
        with path.open("r", encoding=encoding, newline="") as source:
            return _parse_lines(source, options, path, cancelled, progress)
    except UnicodeDecodeError as error:
        raise InvalidEncodingError(f"Cannot decode input as {encoding}") from error


def parse_text(
    text: str,
    options: ImportOptions = DEFAULT_IMPORT_OPTIONS,
    source: Path | None = None,
    cancelled: Callable[[], bool] | None = None,
    progress: Callable[[int], None] | None = None,
) -> Dataset:
    from io import StringIO

    return _parse_lines(StringIO(text, newline=""), options, source, cancelled, progress)


def _parse_lines(
    lines: Iterable[str],
    options: ImportOptions,
    source: Path | None,
    cancelled: Callable[[], bool] | None,
    progress: Callable[[int], None] | None,
) -> Dataset:
    if options.inconsistent_rows not in {"error", "pad", "truncate"}:
        raise UnsupportedFormatError(
            f"Unknown inconsistent row policy: {options.inconsistent_rows}"
        )
    try:
        if options.delimiter is None:
            delimiter = detect_delimiter(_sample_lines(lines, cancelled))
            lines = _rewindable_lines(lines)
        else:
            delimiter = options.delimiter

        if delimiter == "whitespace":
            records = _whitespace_records(lines, cancelled)
        else:
            if len(delimiter) != 1:
                raise UnsupportedFormatError("Delimiter must be one character or 'whitespace'")
            records = _csv_records(lines, delimiter, cancelled)

        rows: list[list[str]] = []
        issues: list[tuple[int, int, int]] = []
        width: int | None = None
        max_width = 0
        for number, row in records:
            if not row:
                continue
            if width is None:
                width = len(row)
            elif len(row) != width:
                issues.append((number, width, len(row)))
            max_width = max(max_width, len(row))
            if options.inconsistent_rows == "truncate" and width is not None:
                row = row[:width]
            rows.append(row)
            if progress is not None and len(rows) % 5_000 == 0:
                progress(len(rows))
        if progress is not None:
            progress(len(rows))
    except csv.Error as error:
        raise MalformedQuotesError(str(error)) from error

    if not rows:
        return Dataset((), (), source)
    assert width is not None
    if issues and options.inconsistent_rows == "error":
        raise InconsistentRowsError(issues)

    if options.inconsistent_rows == "pad":
        width = max_width
        if options.has_header and len(rows[0]) < width:
            rows[0].extend(
                f"Column {index}" for index in range(len(rows[0]) + 1, width + 1)
            )
        rows = [row + [""] * (width - len(row)) for row in rows]
    if options.has_header:
        columns = rows.pop(0)
        if len(columns) < width:
            columns.extend(f"Column {index}" for index in range(len(columns) + 1, width + 1))
    else:
        columns = [f"Column {index}" for index in range(1, width + 1)]
    return Dataset(tuple(columns), tuple(tuple(row) for row in rows), source)


def _sample_lines(lines: Iterable[str], cancelled: Callable[[], bool] | None) -> list[str]:
    sample: list[str] = []
    for line in lines:
        if cancelled and cancelled():
            raise OperationCancelledError("Import cancelled")
        if line.strip():
            sample.append(line)
            if len(sample) == 20:
                break
    return sample


def _rewindable_lines(lines: Iterable[str]) -> Iterable[str]:
    seek = getattr(lines, "seek", None)
    if seek is None:
        raise RuntimeError("Automatic delimiter detection requires a seekable input")
    seek(0)
    return lines


def _whitespace_records(
    lines: Iterable[str], cancelled: Callable[[], bool] | None
) -> Iterable[tuple[int, list[str]]]:
    for number, line in enumerate(lines, 1):
        if cancelled and cancelled():
            raise OperationCancelledError("Import cancelled")
        if line.strip():
            yield number, tokenize_whitespace(line.rstrip("\r\n"))


def _csv_records(
    lines: Iterable[str], delimiter: str, cancelled: Callable[[], bool] | None
) -> Iterable[tuple[int, list[str]]]:
    reader = csv.reader(lines, delimiter=delimiter, strict=True)
    for row in reader:
        if cancelled and cancelled():
            raise OperationCancelledError("Import cancelled")
        yield reader.line_num, row


def _detect_encoding(path: Path, requested: str | None) -> str:
    if requested:
        try:
            return codecs.lookup(requested).name
        except LookupError as error:
            raise InvalidEncodingError(f"Unknown encoding: {requested}") from error
    with path.open("rb") as source:
        sample = source.read(_SAMPLE_BYTES)
    if sample.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    try:
        sample.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError as error:
        if error.reason == "unexpected end of data" and error.end == len(sample):
            try:
                sample[: error.start].decode("utf-8")
                return "utf-8"
            except UnicodeDecodeError:
                pass
    try:
        from charset_normalizer import from_bytes

        match = from_bytes(sample).best()
    except ImportError as error:
        raise InvalidEncodingError(
            "Input is not UTF-8; install charset-normalizer or select an encoding"
        ) from error
    if match is None or match.encoding is None:
        raise InvalidEncodingError("Could not detect input encoding")
    return match.encoding
