from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QBrush, QColor

from ..core.models import Dataset


class DatasetTableModel(QAbstractTableModel):
    """A non-copying model, so QTableView can virtualize large datasets."""

    def __init__(self, dataset: Dataset | None = None) -> None:
        super().__init__()
        self._dataset = dataset or Dataset((), ())
        self._original: Dataset | None = None
        self._original_columns: tuple[int | None, ...] = ()
        self._highlight_changes = False

    def set_dataset(
        self,
        dataset: Dataset,
        original: Dataset | None = None,
        highlight_changes: bool = False,
    ) -> None:
        self.beginResetModel()
        self._dataset = dataset
        self._original = original
        self._highlight_changes = highlight_changes
        self._original_columns = _column_mapping(dataset.columns, original.columns) if original else ()
        self.endResetModel()

    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex | None = None
    ) -> int:
        return 0 if parent is not None and parent.isValid() else self._dataset.row_count

    def columnCount(
        self, parent: QModelIndex | QPersistentModelIndex | None = None
    ) -> int:
        return 0 if parent is not None and parent.isValid() else self._dataset.column_count

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and index.isValid():
            return self._dataset.rows[index.row()][index.column()]
        if (
            role == Qt.ItemDataRole.BackgroundRole
            and index.isValid()
            and self._highlight_changes
            and self._original is not None
            and index.row() < self._original.row_count
        ):
            source_column = self._original_columns[index.column()]
            if (
                source_column is not None
                and self._dataset.rows[index.row()][index.column()]
                != self._original.rows[index.row()][source_column]
            ):
                return QBrush(QColor("#fff0b3"))
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < self._dataset.column_count:
            return self._dataset.columns[section]
        if orientation == Qt.Orientation.Vertical:
            return str(section + 1)
        return None


def _column_mapping(
    columns: tuple[str, ...], original: tuple[str, ...]
) -> tuple[int | None, ...]:
    if columns == original:
        return tuple(range(len(columns)))
    mapping: list[int | None] = []
    source_index = 0
    for name in columns:
        while source_index < len(original) and original[source_index] != name:
            source_index += 1
        if source_index == len(original):
            mapping.append(None)
        else:
            mapping.append(source_index)
            source_index += 1
    return tuple(mapping)
