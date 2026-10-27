from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from ..core.errors import OperationCancelledError, TabConvError
from ..core.export import write_dataset
from ..core.models import Dataset, ExportOptions


class BatchExportWorker(QObject):
    succeeded = Signal(int)
    failed = Signal(str)
    progress = Signal(int)
    cancelled = Signal()
    finished = Signal()

    def __init__(
        self,
        datasets: tuple[Dataset, ...],
        output_dir: Path,
        suffix: str,
        options: ExportOptions,
        remove_converted: bool,
    ) -> None:
        super().__init__()
        self._datasets = datasets
        self._output_dir = output_dir
        self._suffix = suffix
        self._options = options
        self._remove_converted = remove_converted

    @Slot()
    def run(self) -> None:
        try:
            for index, dataset in enumerate(self._datasets):
                if QThread.currentThread().isInterruptionRequested():
                    raise OperationCancelledError()
                source = dataset.source
                if source is None:
                    raise TabConvError("Cannot determine a filename for one of the files.")
                stem = source.stem
                if not self._remove_converted:
                    stem += "_converted"
                output = self._output_dir / f"{stem}{self._suffix}"
                write_dataset(
                    dataset,
                    output,
                    self._options,
                    overwrite=True,
                    cancelled=lambda: QThread.currentThread().isInterruptionRequested(),
                    progress=lambda value: self.progress.emit(
                        round((index * 100 + value) / len(self._datasets))
                    ),
                )
            self.succeeded.emit(len(self._datasets))
        except OperationCancelledError:
            self.cancelled.emit()
        except (OSError, TabConvError) as error:
            self.failed.emit(str(error))
        except Exception as error:  # noqa: BLE001 - report unexpected worker errors to the UI
            self.failed.emit(f"Could not export files: {error}")
        finally:
            self.finished.emit()
