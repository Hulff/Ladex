from dataclasses import dataclass, field, replace

from .errors import InvalidTransformationError
from .models import Dataset
from .transforms import ConvertDecimalSeparator, RemoveColumns, ReplaceText
from .transforms.base import Operation


@dataclass(frozen=True, slots=True)
class BatchOperation:
    operation: Operation
    column_names: tuple[str, ...] | None


@dataclass(slots=True)
class BatchHistory:
    """Replay shared column-name operations over a collection of separate files."""

    original: tuple[Dataset, ...]
    _operations: list[BatchOperation] = field(default_factory=list)
    _cursor: int = 0

    def __post_init__(self) -> None:
        if not self.original:
            raise InvalidTransformationError("A batch must contain at least one dataset")

    @property
    def operations(self) -> tuple[BatchOperation, ...]:
        return tuple(self._operations[: self._cursor])

    @property
    def current(self) -> tuple[Dataset, ...]:
        datasets = self.original
        for operation in self.operations:
            datasets = _apply_batch_operation(datasets, operation)
        return datasets

    @property
    def can_undo(self) -> bool:
        return self._cursor > 0

    @property
    def can_redo(self) -> bool:
        return self._cursor < len(self._operations)

    def apply(
        self,
        operation: Operation,
        column_names: tuple[str, ...] | None = None,
    ) -> tuple[Dataset, ...]:
        entry = BatchOperation(operation, column_names)
        result = _apply_batch_operation(self.current, entry)
        del self._operations[self._cursor :]
        self._operations.append(entry)
        self._cursor += 1
        return result

    def undo(self) -> tuple[Dataset, ...]:
        if self.can_undo:
            self._cursor -= 1
        return self.current

    def redo(self) -> tuple[Dataset, ...]:
        if self.can_redo:
            self._cursor += 1
        return self.current

    def reset(self) -> tuple[Dataset, ...]:
        self._operations.clear()
        self._cursor = 0
        return self.original


def _apply_batch_operation(
    datasets: tuple[Dataset, ...], entry: BatchOperation
) -> tuple[Dataset, ...]:
    operation = entry.operation
    names = entry.column_names
    results: list[Dataset] = []
    for dataset in datasets:
        indexes = tuple(
            index
            for index, name in enumerate(dataset.columns)
            if names is None or name in names
        )
        if isinstance(operation, RemoveColumns):
            if names is None:
                selected = tuple(
                    dataset.columns[index]
                    for index in operation.columns
                    if index < dataset.column_count
                )
                indexes = tuple(
                    index for index, name in enumerate(dataset.columns) if name in selected
                )
            results.append(RemoveColumns(indexes).apply(dataset) if indexes else dataset)
        elif isinstance(operation, (ReplaceText, ConvertDecimalSeparator)):
            results.append(replace(operation, columns=indexes).apply(dataset))
        else:
            results.append(operation.apply(dataset))
    return tuple(results)
