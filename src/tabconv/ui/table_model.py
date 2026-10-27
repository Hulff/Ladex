from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from ..core.models import Dataset


class DatasetTableModel(QAbstractTableModel):
    """A non-copying model, so QTableView can virtualize large datasets."""

    def __init__(self, dataset: Dataset | None = None) -> None:
        super().__init__()
        self._dataset = dataset or Dataset((), ())

    def set_dataset(self, dataset: Dataset) -> None:
        self.beginResetModel()
        self._dataset = dataset
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else self._dataset.row_count

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else self._dataset.column_count

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and index.isValid():
            return self._dataset.rows[index.row()][index.column()]
        return None

    def headerData(  # noqa: N802
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
