from dataclasses import dataclass

from ..errors import InvalidTransformationError
from ..models import Dataset


@dataclass(frozen=True, slots=True)
class ReplaceText:
    find: str
    replacement: str
    columns: tuple[int, ...] | None = None
    case_sensitive: bool = True

    def __post_init__(self) -> None:
        if not self.find:
            raise InvalidTransformationError("Find text cannot be empty")
        if self.columns is not None and any(index < 0 for index in self.columns):
            raise InvalidTransformationError("Column indexes must be non-negative")

    def apply(self, dataset: Dataset) -> Dataset:
        indexes = _selected_indexes(dataset, self.columns)
        rows = tuple(
            tuple(
                _replace(value, self.find, self.replacement, self.case_sensitive)
                if index in indexes
                else value
                for index, value in enumerate(row)
            )
            for row in dataset.rows
        )
        return Dataset(dataset.columns, rows, dataset.source)

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "replace_text",
            "find": self.find,
            "replacement": self.replacement,
            "columns": list(self.columns) if self.columns is not None else None,
            "case_sensitive": self.case_sensitive,
        }


def _replace(value: str, find: str, replacement: str, case_sensitive: bool) -> str:
    if case_sensitive:
        return value.replace(find, replacement)
    folded_find = find.casefold()
    output: list[str] = []
    offset = 0
    while offset < len(value):
        match = value[offset : offset + len(find)]
        if match.casefold() == folded_find:
            output.append(replacement)
            offset += len(find)
        else:
            output.append(value[offset])
            offset += 1
    return "".join(output)


def _selected_indexes(dataset: Dataset, columns: tuple[int, ...] | None) -> frozenset[int]:
    selected = frozenset(range(dataset.column_count) if columns is None else columns)
    if any(index >= dataset.column_count for index in selected):
        raise InvalidTransformationError("Selected column index is out of range")
    return selected
