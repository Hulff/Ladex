from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from ..core.batch import BatchHistory
from ..core.errors import TabConvError
from ..core.transforms.base import Operation


class HistoryWorker(QObject):
    completed = Signal(object, object)
    failed = Signal(object, str)
    finished = Signal()

    def __init__(
        self,
        history: BatchHistory,
        action: str,
        operation: Operation | None = None,
        column_names: tuple[str, ...] | None = None,
    ) -> None:
        super().__init__()
        self._history = history
        self._action = action
        self._operation = operation
        self._column_names = column_names

    @Slot()
    def run(self) -> None:
        try:
            if self._action == "apply" and self._operation is not None:
                dataset = self._history.apply(self._operation, self._column_names)
            elif self._action == "undo":
                dataset = self._history.undo()
            elif self._action == "redo":
                dataset = self._history.redo()
            elif self._action == "reset":
                dataset = self._history.reset()
            else:
                raise ValueError(f"Unknown history action: {self._action}")
        except TabConvError as error:
            self.failed.emit(self._history, str(error))
        except Exception as error:  # noqa: BLE001 - report unexpected worker errors to the UI
            self.failed.emit(self._history, str(error))
        else:
            self.completed.emit(self._history, dataset)
        finally:
            self.finished.emit()
