from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Dataset:
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    source: Path | None = None

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.columns)


@dataclass(frozen=True, slots=True)
class ImportOptions:
    delimiter: str | None = None
    encoding: str | None = None
    has_header: bool = True
    inconsistent_rows: str = "error"


@dataclass(frozen=True, slots=True)
class ExportOptions:
    delimiter: str | None = None
    include_header: bool = True
    line_ending: str = "\n"
    encoding: str = "utf-8"
