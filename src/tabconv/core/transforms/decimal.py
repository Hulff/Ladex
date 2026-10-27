import re
from dataclasses import dataclass

from ..errors import InvalidTransformationError
from ..models import Dataset
from .replace import _selected_indexes

_NUMBER = re.compile(r"^[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)$")


@dataclass(frozen=True, slots=True)
class ConvertDecimalSeparator:
    source_separator: str
    target_separator: str
    columns: tuple[int, ...] | None = None
    thousands_separator: str | None = None

    def __post_init__(self) -> None:
        if self.source_separator not in {".", ","} or self.target_separator not in {".", ","}:
            raise InvalidTransformationError("Decimal separators must be '.' or ','")
        if self.source_separator == self.target_separator:
            raise InvalidTransformationError("Source and target separators must differ")
        if self.thousands_separator not in {None, ".", ",", " "}:
            raise InvalidTransformationError("Thousands separator must be none, '.', ',' or space")
        if self.thousands_separator == self.source_separator:
            raise InvalidTransformationError("Thousands separator cannot match the decimal separator")
        if self.columns is not None and any(index < 0 for index in self.columns):
            raise InvalidTransformationError("Column indexes must be non-negative")

    def apply(self, dataset: Dataset) -> Dataset:
        indexes = _selected_indexes(dataset, self.columns)
        rows = tuple(
            tuple(
                self._convert(value) if index in indexes else value
                for index, value in enumerate(row)
            )
            for row in dataset.rows
        )
        return Dataset(dataset.columns, rows, dataset.source)

    def _convert(self, value: str) -> str:
        leading = value[: len(value) - len(value.lstrip())]
        trailing = value[len(value.rstrip()) :]
        candidate = value.strip()
        if (
            self.source_separator not in candidate
            or candidate.count(self.source_separator) > 1
        ):
            return value
        if not _valid_number(candidate, self.source_separator, self.thousands_separator):
            return value
        if self.thousands_separator:
            candidate = candidate.replace(self.thousands_separator, "")
        converted = candidate.replace(self.source_separator, self.target_separator)
        return f"{leading}{converted}{trailing}"

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "convert_decimal_separator",
            "source_separator": self.source_separator,
            "target_separator": self.target_separator,
            "columns": list(self.columns) if self.columns is not None else None,
            "thousands_separator": self.thousands_separator,
        }


def _valid_number(value: str, decimal: str, thousands: str | None) -> bool:
    if thousands is None:
        return bool(_NUMBER.fullmatch(value))
    signless = value[1:] if value.startswith(("+", "-")) else value
    integer, separator, fraction = signless.partition(decimal)
    if separator and (not fraction or decimal in fraction):
        return False
    if not integer or (not integer.isdigit() and thousands not in integer):
        return False
    if thousands in integer:
        groups = integer.split(thousands)
        if not groups[0].isdigit() or not 1 <= len(groups[0]) <= 3:
            return False
        if any(len(group) != 3 or not group.isdigit() for group in groups[1:]):
            return False
    elif not integer.isdigit():
        return False
    return not separator or fraction.isdigit()
