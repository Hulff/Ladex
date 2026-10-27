from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Qt, QUrl
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ..core.models import Dataset, ImportOptions
from .load_worker import LoadWorker
from .table_model import DatasetTableModel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._path: Path | None = None
        self._thread: QThread | None = None
        self._model = DatasetTableModel()
        self.setWindowTitle("Tabular Text Converter")
        self.setMinimumSize(900, 580)
        self.setAcceptDrops(True)
        self._build_ui()

    def _build_ui(self) -> None:
        open_action = QAction("Open…", self, shortcut=QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.choose_file)
        self.menuBar().addAction(open_action)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setFixedWidth(245)
        controls = QVBoxLayout(sidebar)
        controls.addWidget(QLabel("Import settings"))
        form = QFormLayout()
        self.delimiter = QComboBox()
        self.delimiter.addItem("Auto-detect", None)
        self.delimiter.addItem("Comma (,)", ",")
        self.delimiter.addItem("Semicolon (;)", ";")
        self.delimiter.addItem("Tab", "\t")
        self.delimiter.addItem("Whitespace", "whitespace")
        self.delimiter.currentIndexChanged.connect(self.reload)
        form.addRow("Delimiter", self.delimiter)
        self.encoding = QComboBox()
        self.encoding.addItem("Auto-detect", None)
        for value in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            self.encoding.addItem(value, value)
        self.encoding.currentIndexChanged.connect(self.reload)
        form.addRow("Encoding", self.encoding)
        self.header = QCheckBox("First row is a header")
        self.header.setChecked(True)
        self.header.toggled.connect(self.reload)
        form.addRow(self.header)
        controls.addLayout(form)
        controls.addSpacing(12)
        button = QPushButton("Open file…")
        button.clicked.connect(self.choose_file)
        controls.addWidget(button)
        controls.addStretch()
        hint = QLabel("Choose a file or drop a CSV, TSV, or TXT file anywhere in this window.")
        hint.setWordWrap(True)
        controls.addWidget(hint)

        preview = QVBoxLayout()
        self.empty = QLabel("Open or drop a tabular text file to see its preview.")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table = QTableView()
        self.table.setModel(self._model)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setVisible(False)
        self.summary = QLabel("No file selected")
        preview.addWidget(self.empty, 1)
        preview.addWidget(self.table, 1)
        preview.addWidget(self.summary)
        layout.addWidget(sidebar)
        layout.addLayout(preview, 1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if self._dropped_path(event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        path = self._dropped_path(event.mimeData().urls())
        if path:
            self.open_path(path)
            event.acceptProposedAction()

    @staticmethod
    def _dropped_path(urls: list[QUrl]) -> Path | None:
        for url in urls:
            path = Path(url.toLocalFile())
            if path.suffix.lower() in {".csv", ".tsv", ".txt"} and path.is_file():
                return path
        return None

    def choose_file(self) -> None:
        name, _ = QFileDialog.getOpenFileName(
            self, "Open tabular text", "", "Tabular text (*.csv *.tsv *.txt)"
        )
        if name:
            self.open_path(Path(name))

    def open_path(self, path: Path) -> None:
        self._path = path
        self.reload()

    def reload(self) -> None:
        if self._path is None or (self._thread is not None and self._thread.isRunning()):
            return
        options = ImportOptions(
            delimiter=self.delimiter.currentData(),
            encoding=self.encoding.currentData(),
            has_header=self.header.isChecked(),
        )
        self.statusBar().showMessage(f"Loading {self._path.name}…")
        self._thread = QThread(self)
        worker = LoadWorker(self._path, options)
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.loaded.connect(self.show_dataset)
        worker.failed.connect(self.show_error)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_thread)
        self._thread.start()

    def _clear_thread(self) -> None:
        self._thread = None

    def show_dataset(self, dataset: Dataset) -> None:
        self._model.set_dataset(dataset)
        self.empty.setVisible(False)
        self.table.setVisible(True)
        self.summary.setText(
            f"{dataset.source}  •  {dataset.row_count:,} rows × {dataset.column_count:,} columns"
        )
        self.statusBar().showMessage("Preview ready")

    def show_error(self, message: str) -> None:
        self.statusBar().showMessage("Could not load file")
        QMessageBox.warning(self, "Could not load file", message)
