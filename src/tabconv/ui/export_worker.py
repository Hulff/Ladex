from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from ..core.errors import OperationCancelledError, TabConvError
from ..core.export import write_dataset
from ..core.models import Dataset, ExportOptions


class ExportWorker(QObject):
    succeeded = Signal(str)
    failed = Signal(str)
    progress = Signal(int)
    cancelled = Signal()
    finished = Signal()

    def __init__(
        self,
        dataset: Dataset,
        path: Path,
        options: ExportOptions,
        overwrite: bool,
    ) -> None:
        super().__init__()
        self._dataset = dataset
        self._path = path
        self._options = options
        self._overwrite = overwrite

    @Slot()
    def run(self) -> None:
        try:
            write_dataset(
                self._dataset,
                self._path,
                self._options,
                overwrite=self._overwrite,
                cancelled=lambda: QThread.currentThread().isInterruptionRequested(),
                progress=self.progress.emit,
            )
        except OperationCancelledError:
            self.cancelled.emit()
        except (OSError, TabConvError) as error:
            self.failed.emit(str(error))
        except Exception as error:  # noqa: BLE001 - report unexpected worker errors to the UI
            self.failed.emit(f"Could not export to {self._path}: {error}")
        else:
            self.succeeded.emit(str(self._path))
        finally:
            self.finished.emit()
