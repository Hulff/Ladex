from __future__ import annotations

import csv
import os
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path

from ..errors import ExportError, OperationCancelledError
from ..models import Dataset, ExportOptions

DEFAULT_EXPORT_OPTIONS = ExportOptions()


def write_dataset(
    dataset: Dataset,
    path: Path,
    options: ExportOptions = DEFAULT_EXPORT_OPTIONS,
    *,
    overwrite: bool = False,
    cancelled: Callable[[], bool] | None = None,
    progress: Callable[[int], None] | None = None,
) -> None:
    """Write a dataset atomically, refusing to replace an existing file by default."""
    suffix = path.suffix.lower()
    if suffix not in {".csv", ".tsv", ".txt", ".xlsx"}:
        raise ExportError(f"Unsupported output format: {suffix or '(none)'}")
    if options.line_ending not in {"\n", "\r\n"}:
        raise ExportError("Line ending must be LF or CRLF")
    if not options.encoding:
        raise ExportError("Encoding cannot be empty")
    delimiter = options.delimiter
    if delimiter is None:
        delimiter = {".csv": ",", ".tsv": "\t", ".txt": " "}.get(suffix)
    if suffix != ".xlsx" and (delimiter is None or len(delimiter) != 1):
        raise ExportError("Text delimiter must be one character")
    if path.exists() and not overwrite:
        raise ExportError(f"File already exists: {path}")
    if not path.parent.is_dir():
        raise ExportError(f"Output folder does not exist: {path.parent}")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{path.stem}.", suffix=path.suffix, dir=path.parent, delete=False
        ) as temporary:
            temp_path = Path(temporary.name)
        if suffix == ".xlsx":
            _write_xlsx(dataset, temp_path, options, cancelled, progress)
        else:
            _write_delimited(
                dataset,
                temp_path,
                options,
                delimiter if delimiter is not None else "",
                cancelled,
                progress,
            )
        if overwrite:
            os.replace(temp_path, path)
        else:
            # Linking the completed file creates the destination only if it is still absent.
            os.link(temp_path, path)
            temp_path.unlink()
    except OperationCancelledError:
        raise
    except (OSError, UnicodeError, LookupError, csv.Error, ImportError) as error:
        raise ExportError(f"Could not export to {path}: {error}") from error
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _rows(dataset: Dataset, options: ExportOptions) -> Iterable[tuple[str, ...]]:
    if options.include_header:
        yield dataset.columns
    yield from dataset.rows


def _write_delimited(
    dataset: Dataset,
    path: Path,
    options: ExportOptions,
    delimiter: str,
    cancelled: Callable[[], bool] | None,
    progress: Callable[[int], None] | None,
) -> None:
    total = dataset.row_count + int(options.include_header)
    with path.open("w", encoding=options.encoding, newline="") as output:
        writer = csv.writer(output, delimiter=delimiter, lineterminator=options.line_ending)
        for number, row in enumerate(_rows(dataset, options), 1):
            if cancelled and cancelled():
                raise OperationCancelledError("Export cancelled")
            writer.writerow(row)
            _report_progress(number, total, progress)
    if total == 0:
        _report_progress(0, total, progress)


def _write_xlsx(
    dataset: Dataset,
    path: Path,
    options: ExportOptions,
    cancelled: Callable[[], bool] | None,
    progress: Callable[[int], None] | None,
) -> None:
    from openpyxl import Workbook
    from openpyxl.cell import WriteOnlyCell

    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Data")
    total = dataset.row_count + int(options.include_header)
    for number, row in enumerate(_rows(dataset, options), 1):
        if cancelled and cancelled():
            raise OperationCancelledError("Export cancelled")
        cells = []
        for value in row:
            cell = WriteOnlyCell(sheet, value=value)
            cell.data_type = "s"
            cells.append(cell)
        sheet.append(cells)
        _report_progress(number, total, progress)
    if total == 0:
        _report_progress(0, total, progress)
    workbook.save(path)


def _report_progress(number: int, total: int, progress: Callable[[int], None] | None) -> None:
    if progress and (number == 0 or number == total or number % max(1, total // 100) == 0):
        progress(100 if total == 0 else min(100, number * 100 // total))
