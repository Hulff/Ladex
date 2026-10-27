from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from ..core.errors import InconsistentRowsError, OperationCancelledError, TabConvError
from ..core.models import ImportOptions
from ..core.parsing.reader import read_file


class LoadWorker(QObject):
    loaded = Signal(object)
    failed = Signal(str)
    progress = Signal(int)
    inconsistent = Signal(object)
    cancelled = Signal()
    finished = Signal()

    def __init__(self, path: Path, options: ImportOptions) -> None:
        super().__init__()
        self._path = path
        self._options = options

    @Slot()
    def run(self) -> None:
        try:
            self.loaded.emit(
                read_file(
                    self._path,
                    self._options,
                    cancelled=lambda: QThread.currentThread().isInterruptionRequested(),
                    progress=self.progress.emit,
                )
            )
        except InconsistentRowsError as error:
            self.inconsistent.emit(error.issues)
        except OperationCancelledError:
            self.cancelled.emit()
        except (OSError, TabConvError) as error:
            self.failed.emit(str(error))
        except Exception as error:  # noqa: BLE001 - make unexpected import failures visible
            self.failed.emit(f"Could not load {self._path}: {error}")
        finally:
            self.finished.emit()
