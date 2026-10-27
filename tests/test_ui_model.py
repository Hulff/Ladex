from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush

from tabconv.core.models import Dataset
from tabconv.ui.table_model import DatasetTableModel


def test_processed_cell_highlighting() -> None:
    original = Dataset(("amount",), (("1.25",),))
    processed = Dataset(("amount",), (("1,25",),))
    model = DatasetTableModel()
    model.set_dataset(processed, original, highlight_changes=True)
    assert isinstance(model.data(model.index(0, 0), Qt.ItemDataRole.BackgroundRole), QBrush)


def test_removed_column_highlighting_tracks_remaining_columns() -> None:
    original = Dataset(("drop", "keep"), (("x", "1"),))
    processed = Dataset(("keep",), (("2",),))
    model = DatasetTableModel()
    model.set_dataset(processed, original, highlight_changes=True)
    assert isinstance(model.data(model.index(0, 0), Qt.ItemDataRole.BackgroundRole), QBrush)
