from dataclasses import dataclass

from ..errors import InvalidTransformationError
from ..models import Dataset


@dataclass(frozen=True, slots=True)
class RemoveColumns:
    columns: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.columns:
            raise InvalidTransformationError("Select at least one column to remove")
        if any(index < 0 for index in self.columns):
            raise InvalidTransformationError("Column indexes must be non-negative")

    def apply(self, dataset: Dataset) -> Dataset:
        removed = frozenset(self.columns)
        if any(index >= dataset.column_count for index in removed):
            raise InvalidTransformationError("Selected column index is out of range")
        kept = tuple(index for index in range(dataset.column_count) if index not in removed)
        return Dataset(
            tuple(dataset.columns[index] for index in kept),
            tuple(tuple(row[index] for index in kept) for row in dataset.rows),
            dataset.source,
        )

    def to_dict(self) -> dict[str, object]:
        return {"type": "remove_columns", "columns": list(self.columns)}
