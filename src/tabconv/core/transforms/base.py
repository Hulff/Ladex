from typing import Protocol

from ..models import Dataset


class Operation(Protocol):
    """A serializable operation that returns a new dataset."""

    def apply(self, dataset: Dataset) -> Dataset: ...

    def to_dict(self) -> dict[str, object]: ...


def apply_operation(dataset: Dataset, operation: Operation) -> Dataset:
    """Apply an operation while ensuring the imported dataset remains untouched."""
    return operation.apply(dataset)
