from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from ..core.errors import InconsistentRowsError, OperationCancelledError, TabConvError
from ..core.models import Dataset, ImportOptions
from ..core.parsing.reader import read_file


class BatchLoadWorker(QObject):
    loaded = Signal(object)
    failed = Signal(str)
    progress = Signal(str, int)
    inconsistent = Signal(str, object)
    cancelled = Signal()
    finished = Signal()

    def __init__(self, paths: tuple[Path, ...], options: ImportOptions) -> None:
        super().__init__()
        self._paths = paths
        self._options = options

    @Slot()
    def run(self) -> None:
        datasets: list[Dataset] = []
        try:
            for path in self._paths:
                if QThread.currentThread().isInterruptionRequested():
                    raise OperationCancelledError("Import cancelled")

                def report_progress(count: int, filename: str = path.name) -> None:
                    self.progress.emit(filename, count)

                try:
                    dataset = read_file(
                        path,
                        self._options,
                        cancelled=lambda: QThread.currentThread().isInterruptionRequested(),
                        progress=report_progress,
                    )
                except InconsistentRowsError as error:
                    self.inconsistent.emit(path.name, error.issues)
                    return
                datasets.append(dataset)
        except OperationCancelledError:
            self.cancelled.emit()
        except (OSError, TabConvError) as error:
            self.failed.emit(str(error))
        except Exception as error:  # noqa: BLE001 - report unexpected import failures to the UI
            self.failed.emit(f"Could not load batch: {error}")
        else:
            self.loaded.emit(tuple(datasets))
        finally:
            self.finished.emit()
