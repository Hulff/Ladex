from dataclasses import dataclass, field

from .models import Dataset
from .transforms import Operation
from .transforms.columns import RemoveColumns
from .transforms.decimal import ConvertDecimalSeparator
from .transforms.replace import ReplaceText

_OPERATION_TYPES: dict[str, type[Operation]] = {
    "replace_text": ReplaceText,
    "convert_decimal_separator": ConvertDecimalSeparator,
    "remove_columns": RemoveColumns,
}


def operation_from_dict(data: dict[str, object]) -> Operation:
    """Restore a supported operation from its JSON-compatible representation."""
    operation_type = data.get("type")
    if not isinstance(operation_type, str) or operation_type not in _OPERATION_TYPES:
        raise ValueError(f"Unknown operation type: {operation_type!r}")
    operation_class = _OPERATION_TYPES[operation_type]
    values = {key: value for key, value in data.items() if key != "type"}
    if "columns" in values and isinstance(values["columns"], list):
        values["columns"] = tuple(values["columns"])
    return operation_class(**values)


@dataclass(slots=True)
class DatasetHistory:
    """Keep an original dataset and deterministically replay its operation history."""

    original: Dataset
    _operations: list[Operation] = field(default_factory=list)
    _cursor: int = 0

    @property
    def operations(self) -> tuple[Operation, ...]:
        return tuple(self._operations[: self._cursor])

    @property
    def current(self) -> Dataset:
        dataset = self.original
        for operation in self.operations:
            dataset = operation.apply(dataset)
        return dataset

    @property
    def can_undo(self) -> bool:
        return self._cursor > 0

    @property
    def can_redo(self) -> bool:
        return self._cursor < len(self._operations)

    def apply(self, operation: Operation) -> Dataset:
        result = operation.apply(self.current)
        del self._operations[self._cursor :]
        self._operations.append(operation)
        self._cursor += 1
        return result

    def undo(self) -> Dataset:
        if self.can_undo:
            self._cursor -= 1
        return self.current

    def redo(self) -> Dataset:
        if self.can_redo:
            self._cursor += 1
        return self.current

    def reset(self) -> Dataset:
        self._operations.clear()
        self._cursor = 0
        return self.original

    def serialize(self) -> list[dict[str, object]]:
        return [operation.to_dict() for operation in self.operations]

    def load(self, operations: list[dict[str, object]]) -> Dataset:
        restored = [operation_from_dict(item) for item in operations]
        dataset = self.original
        for operation in restored:
            dataset = operation.apply(dataset)
        self._operations = restored
        self._cursor = len(restored)
        return dataset
