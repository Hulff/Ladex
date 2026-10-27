from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from ..core.errors import TabConvError
from ..core.models import ImportOptions
from ..core.parsing.reader import read_file


class LoadWorker(QObject):
    loaded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, path: Path, options: ImportOptions) -> None:
        super().__init__()
        self._path = path
        self._options = options

    @Slot()
    def run(self) -> None:
        try:
            self.loaded.emit(read_file(self._path, self._options))
        except (OSError, TabConvError) as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()
