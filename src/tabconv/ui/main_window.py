from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDropEvent, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ..core.errors import TabConvError
from ..core.history import DatasetHistory
from ..core.models import Dataset, ExportOptions, ImportOptions
from ..core.transforms import ConvertDecimalSeparator, RemoveColumns, ReplaceText
from ..core.transforms.base import Operation
from .export_worker import ExportWorker
from .history_worker import HistoryWorker
from .load_worker import LoadWorker
from .table_model import DatasetTableModel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._path: Path | None = None
        self._thread: QThread | None = None
        self._history_thread: QThread | None = None
        self._active_history: DatasetHistory | None = None
        self._model = DatasetTableModel()
        self._history: DatasetHistory | None = None
        self._original: Dataset | None = None
        self._current_dataset: Dataset | None = None
        self._column_names: tuple[str, ...] | None = None
        self._row_policy = "error"
        self._pending_reload = False
        self._export_thread: QThread | None = None
        self._closing = False
        self.setWindowTitle("Tabular Text Converter")
        self.setMinimumSize(900, 580)
        self.setAcceptDrops(True)
        self._build_ui()

    def _build_ui(self) -> None:
        open_action = QAction(
            "Open…", self, shortcut=QKeySequence(QKeySequence.StandardKey.Open)
        )
        open_action.triggered.connect(self.choose_file)
        self.menuBar().addAction(open_action)
        self.undo_action = QAction(
            "Undo", self, shortcut=QKeySequence(QKeySequence.StandardKey.Undo)
        )
        self.undo_action.triggered.connect(self.undo)
        self.redo_action = QAction(
            "Redo", self, shortcut=QKeySequence(QKeySequence.StandardKey.Redo)
        )
        self.redo_action.triggered.connect(self.redo)
        self.export_action = QAction(
            "Export…", self, shortcut=QKeySequence(QKeySequence.StandardKey.Save)
        )
        self.export_action.triggered.connect(self.export_current)
        self.export_shortcut_action = QAction(
            "Export…", self, shortcut=QKeySequence("Ctrl+E")
        )
        self.export_shortcut_action.triggered.connect(self.export_current)
        for action in (self.undo_action, self.redo_action, self.export_action, self.export_shortcut_action):
            action.setEnabled(False)
        for action in (self.undo_action, self.redo_action, self.export_action):
            self.addAction(action)
        self.addAction(self.export_shortcut_action)

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
        controls.addSpacing(10)

        controls.addWidget(QLabel("Transformations"))
        self.view_mode = QComboBox()
        self.view_mode.addItem("Processed", "processed")
        self.view_mode.addItem("Original", "original")
        self.view_mode.currentIndexChanged.connect(self._refresh_view)
        controls.addWidget(self.view_mode)

        history_buttons = QHBoxLayout()
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self.undo)
        self.undo_button.setEnabled(False)
        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self.redo)
        self.redo_button.setEnabled(False)
        history_buttons.addWidget(self.undo_button)
        history_buttons.addWidget(self.redo_button)
        controls.addLayout(history_buttons)
        self.reset_button = QPushButton("Reset changes")
        self.reset_button.clicked.connect(self.reset_transformations)
        self.reset_button.setEnabled(False)
        controls.addWidget(self.reset_button)
        controls.addWidget(QLabel("Applied operations"))
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(110)
        controls.addWidget(self.history_list)

        self.operation_columns = QComboBox()
        self.operation_columns.addItem("All columns", None)
        self.operation_columns.setEnabled(False)
        controls.addWidget(self.operation_columns)

        transform_form = QFormLayout()
        self.find_text = QLineEdit()
        self.find_text.setPlaceholderText("Text to find")
        transform_form.addRow("Find", self.find_text)
        self.replacement_text = QLineEdit()
        self.replacement_text.setPlaceholderText("Replacement")
        transform_form.addRow("Replace", self.replacement_text)
        self.case_sensitive = QCheckBox("Case sensitive")
        self.case_sensitive.setChecked(True)
        transform_form.addRow(self.case_sensitive)
        controls.addLayout(transform_form)
        self.replace_button = QPushButton("Replace text")
        self.replace_button.clicked.connect(self.replace_text)
        controls.addWidget(self.replace_button)

        decimal_form = QFormLayout()
        self.decimal_direction = QComboBox()
        self.decimal_direction.addItem("Point → comma", (".", ","))
        self.decimal_direction.addItem("Comma → point", (",", "."))
        decimal_form.addRow("Decimal", self.decimal_direction)
        self.thousands = QComboBox()
        self.thousands.addItem("None", None)
        self.thousands.addItem("Period", ".")
        self.thousands.addItem("Comma", ",")
        self.thousands.addItem("Space", " ")
        decimal_form.addRow("Thousands", self.thousands)
        controls.addLayout(decimal_form)
        self.decimal_button = QPushButton("Convert decimals")
        self.decimal_button.clicked.connect(self.convert_decimals)
        controls.addWidget(self.decimal_button)

        controls.addWidget(QLabel("Columns to remove"))
        self.remove_columns = QComboBox()
        self.remove_columns.setEnabled(False)
        controls.addWidget(self.remove_columns)
        self.remove_button = QPushButton("Remove selected column")
        self.remove_button.clicked.connect(self.remove_selected_column)
        controls.addWidget(self.remove_button)
        self.export_button = QPushButton("Export processed data…")
        self.export_button.clicked.connect(self.export_current)
        self.export_button.setEnabled(False)
        controls.addWidget(self.export_button)
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
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setWidget(sidebar)
        sidebar_scroll.setMinimumWidth(260)
        layout.addWidget(sidebar_scroll)
        layout.addLayout(preview, 1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setVisible(False)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_current_operation)
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.statusBar().addPermanentWidget(self.cancel_button)
        self.statusBar().showMessage("Ready")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._dropped_path(event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
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
        self._row_policy = "error"
        self.reload()

    def reload(self) -> None:
        if self._closing or self._path is None:
            return
        if self._thread is not None:
            self._pending_reload = True
            if self._thread.isRunning():
                self._thread.requestInterruption()
            else:
                QTimer.singleShot(0, self.reload)
            return
        options = ImportOptions(
            delimiter=self.delimiter.currentData(),
            encoding=self.encoding.currentData(),
            has_header=self.header.isChecked(),
            inconsistent_rows=self._row_policy,
        )
        self.statusBar().showMessage(f"Loading {self._path.name}…")
        self._show_progress(indeterminate=True)
        self._thread = QThread(self)
        worker = LoadWorker(self._path, options)
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.loaded.connect(self.show_dataset)
        worker.failed.connect(self.show_error)
        worker.inconsistent.connect(self.resolve_inconsistent_rows)
        worker.progress.connect(self._load_progress)
        worker.cancelled.connect(self._load_cancelled)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_thread)
        self._thread.start()

    def _clear_thread(self) -> None:
        self._thread = None
        self._hide_progress_if_idle()
        self._finish_close_if_idle()
        if self._pending_reload and not self._closing:
            self._pending_reload = False
            self.reload()

    def show_dataset(self, dataset: Dataset) -> None:
        self._original = dataset
        self._current_dataset = dataset
        self._history = DatasetHistory(dataset)
        self._column_names = None
        self._refresh_view()
        self.empty.setVisible(False)
        self.table.setVisible(True)
        self.export_button.setEnabled(True)
        self.statusBar().showMessage("Preview ready")

    def _refresh_view(self) -> None:
        if self._history is None or self._original is None:
            self._set_transform_controls_enabled(False)
            return
        processed = self._current_dataset
        if processed is None:
            return
        self._sync_column_choices(processed.columns)
        show_original = self.view_mode.currentData() == "original"
        dataset = self._original if show_original else processed
        self._model.set_dataset(
            dataset,
            original=self._original,
            highlight_changes=not show_original,
        )
        self.summary.setText(
            f"{dataset.source}  •  {dataset.row_count:,} rows × "
            f"{dataset.column_count:,} columns"
            f"  •  {'Original' if show_original else f'{len(self._history.operations)} change(s)'}"
        )
        history_ready = self._history_thread is None
        self.undo_button.setEnabled(history_ready and self._history.can_undo)
        self.redo_button.setEnabled(history_ready and self._history.can_redo)
        self.reset_button.setEnabled(
            history_ready and (bool(self._history.operations) or self._history.can_redo)
        )
        self.undo_action.setEnabled(history_ready and self._history.can_undo)
        self.redo_action.setEnabled(history_ready and self._history.can_redo)
        can_export = self._history_thread is None and self._export_thread is None
        self.export_action.setEnabled(can_export)
        self.export_shortcut_action.setEnabled(can_export)
        self.history_list.clear()
        for operation in self._history.operations:
            self.history_list.addItem(self._describe_operation(operation))
        can_transform = not show_original and self._history_thread is None
        self._set_transform_controls_enabled(can_transform)
        self.remove_columns.setEnabled(can_transform and bool(processed.columns))
        self.export_button.setEnabled(self._history_thread is None and self._export_thread is None)

    def _sync_column_choices(self, columns: tuple[str, ...]) -> None:
        if columns == self._column_names:
            return
        self._column_names = columns
        self.remove_columns.clear()
        self.operation_columns.clear()
        self.operation_columns.addItem("All columns", None)
        for index, name in enumerate(columns):
            self.remove_columns.addItem(f"{index + 1}: {name}", index)
            self.operation_columns.addItem(f"Only: {index + 1}: {name}", index)
        self.remove_columns.setEnabled(bool(columns))
        self.operation_columns.setEnabled(bool(columns))

    def _set_transform_controls_enabled(self, enabled: bool) -> None:
        self.replace_button.setEnabled(enabled)
        self.decimal_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled and self.remove_columns.count() > 0)

    def _apply_operation(self, operation: Operation) -> None:
        self._queue_history_action("apply", operation)

    def replace_text(self) -> None:
        if not self.find_text.text():
            QMessageBox.information(self, "Find text", "Enter text to find first.")
            return
        columns = self._selected_columns()
        self._apply_operation(
            ReplaceText(
                self.find_text.text(),
                self.replacement_text.text(),
                columns,
                self.case_sensitive.isChecked(),
            )
        )

    def convert_decimals(self) -> None:
        source, target = self.decimal_direction.currentData()
        try:
            operation = ConvertDecimalSeparator(
                source,
                target,
                self._selected_columns(),
                self.thousands.currentData(),
            )
        except TabConvError as error:
            QMessageBox.warning(self, "Cannot apply transformation", str(error))
            return
        self._apply_operation(operation)

    def remove_selected_column(self) -> None:
        index = self.remove_columns.currentData()
        if index is None:
            return
        self._apply_operation(RemoveColumns((index,)))

    def _selected_columns(self) -> tuple[int, ...] | None:
        selected = self.operation_columns.currentData()
        if selected is None or self._history is None:
            return None
        return (selected,)

    def undo(self) -> None:
        self._queue_history_action("undo")

    def redo(self) -> None:
        self._queue_history_action("redo")

    def reset_transformations(self) -> None:
        self._queue_history_action("reset")

    def _queue_history_action(
        self, action: str, operation: Operation | None = None
    ) -> None:
        if self._history is None or self._history_thread is not None:
            return
        self._show_progress(indeterminate=True, cancelable=False)
        self.statusBar().showMessage(
            "Applying transformation…" if action == "apply" else f"{action.title()}…"
        )
        self._history_thread = QThread(self)
        self._active_history = self._history
        worker = HistoryWorker(self._active_history, action, operation)
        worker.moveToThread(self._history_thread)
        self._history_thread.started.connect(worker.run)
        worker.completed.connect(self._history_completed)
        worker.failed.connect(self._history_failed)
        worker.finished.connect(self._history_thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._history_thread.finished.connect(self._clear_history_thread)
        self._history_thread.finished.connect(self._history_thread.deleteLater)
        self._refresh_view()
        self._history_thread.start()

    def _history_completed(self, history: DatasetHistory, dataset: Dataset) -> None:
        if self._history is not history:
            return
        self._current_dataset = dataset
        self.view_mode.setCurrentIndex(0)
        self._refresh_view()
        self.statusBar().showMessage("Transformation history updated")

    def _history_failed(self, history: DatasetHistory, message: str) -> None:
        if self._history is not history:
            return
        self.statusBar().showMessage("Transformation failed")
        QMessageBox.warning(self, "Cannot apply transformation", message)

    def _clear_history_thread(self) -> None:
        self._history_thread = None
        self._active_history = None
        self._refresh_view()
        self._hide_progress_if_idle()
        self._finish_close_if_idle()

    @staticmethod
    def _describe_operation(operation: Operation) -> str:
        if isinstance(operation, ReplaceText):
            return f"Replace {operation.find!r} → {operation.replacement!r}"
        if isinstance(operation, ConvertDecimalSeparator):
            return f"Convert decimal {operation.source_separator} → {operation.target_separator}"
        if isinstance(operation, RemoveColumns):
            return f"Remove column {operation.columns[0] + 1}"
        return type(operation).__name__

    def resolve_inconsistent_rows(self, issues: list[tuple[int, int, int]]) -> None:
        summary = "\n".join(
            f"Line {line}: expected {expected} fields, found {actual}"
            for line, expected, actual in issues[:8]
        )
        if len(issues) > 8:
            summary += f"\n…and {len(issues) - 8} more inconsistent row(s)."
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Rows have different field counts")
        dialog.setText(
            "Choose how to handle inconsistent rows. The original file will not be changed."
        )
        dialog.setDetailedText(summary)
        pad = dialog.addButton("Pad rows", QMessageBox.ButtonRole.AcceptRole)
        truncate = dialog.addButton("Truncate rows", QMessageBox.ButtonRole.DestructiveRole)
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        if dialog.clickedButton() is pad:
            self._row_policy = "pad"
        elif dialog.clickedButton() is truncate:
            self._row_policy = "truncate"
        else:
            self.statusBar().showMessage("Import cancelled")
            return
        if self._thread is None:
            QTimer.singleShot(0, self.reload)
        else:
            self._pending_reload = True

    def export_current(self) -> None:
        if self._history is None or self._export_thread is not None or self._history_thread is not None:
            return
        filters = "CSV (*.csv);;TSV (*.tsv);;Text (*.txt);;Excel workbook (*.xlsx)"
        initial = "converted"
        if self._path is not None:
            initial = f"{self._path.stem}_converted"
        name, selected_filter = QFileDialog.getSaveFileName(
            self, "Export processed data", initial, filters
        )
        if not name:
            return
        path = Path(name)
        suffixes = {
            "CSV (*.csv)": ".csv",
            "TSV (*.tsv)": ".tsv",
            "Text (*.txt)": ".txt",
            "Excel workbook (*.xlsx)": ".xlsx",
        }
        suffix = suffixes.get(selected_filter, ".csv")
        if not path.suffix:
            path = path.with_suffix(suffix)
        elif path.suffix.lower() not in suffixes.values():
            QMessageBox.warning(self, "Export format", "Choose a CSV, TSV, TXT, or XLSX file.")
            return
        options = self._export_options(path.suffix.lower())
        if options is None:
            return
        overwrite = False
        if path.exists():
            answer = QMessageBox.question(
                self,
                "Replace existing file?",
                f"{path} already exists. Replace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            overwrite = True
        if self._path is not None and path.resolve() == self._path.resolve():
            answer = QMessageBox.question(
                self,
                "Replace source file?",
                "This is the imported source file. Replace it with the processed data?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            overwrite = True
        self._start_export(path, options, overwrite)

    def _export_options(self, suffix: str) -> ExportOptions | None:
        if suffix == ".xlsx":
            return ExportOptions()
        dialog = QDialog(self)
        dialog.setWindowTitle("Text export options")
        form = QFormLayout(dialog)
        delimiter = QComboBox()
        delimiter.addItem("Comma (,)", ",")
        delimiter.addItem("Tab", "\t")
        delimiter.addItem("Semicolon (;) ", ";")
        delimiter.addItem("Space", " ")
        default = {".tsv": "\t", ".txt": " ", ".csv": ","}[suffix]
        delimiter.setCurrentIndex(max(0, delimiter.findData(default)))
        form.addRow("Delimiter", delimiter)
        include_header = QCheckBox("Include column names")
        include_header.setChecked(True)
        form.addRow(include_header)
        line_ending = QComboBox()
        line_ending.addItem("LF", "\n")
        line_ending.addItem("CRLF", "\r\n")
        form.addRow("Line ending", line_ending)
        encoding = QComboBox()
        for value in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            encoding.addItem(value, value)
        form.addRow("Encoding", encoding)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return ExportOptions(
            delimiter=delimiter.currentData(),
            include_header=include_header.isChecked(),
            line_ending=line_ending.currentData(),
            encoding=encoding.currentData(),
        )

    def _start_export(
        self, path: Path, options: ExportOptions, overwrite: bool
    ) -> None:
        if self._history is None:
            return
        dataset = self._current_dataset
        if dataset is None:
            return
        self.statusBar().showMessage(f"Exporting to {path.name}…")
        self._show_progress(indeterminate=False)
        self.progress_bar.setValue(0)
        self._export_thread = QThread(self)
        worker = ExportWorker(dataset, path, options, overwrite)
        worker.moveToThread(self._export_thread)
        self._export_thread.started.connect(worker.run)
        worker.progress.connect(self.progress_bar.setValue)
        worker.succeeded.connect(self._export_succeeded)
        worker.failed.connect(self._export_failed)
        worker.cancelled.connect(lambda: self.statusBar().showMessage("Export cancelled"))
        worker.finished.connect(self._export_thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._export_thread.finished.connect(self._clear_export_thread)
        self._export_thread.finished.connect(self._export_thread.deleteLater)
        self._export_thread.start()

    def _export_succeeded(self, path: str) -> None:
        self.statusBar().showMessage(f"Export complete: {path}")

    def _export_failed(self, message: str) -> None:
        self.statusBar().showMessage("Export failed")
        QMessageBox.warning(self, "Export failed", message)

    def _clear_export_thread(self) -> None:
        self._export_thread = None
        self._hide_progress_if_idle()
        self._finish_close_if_idle()

    def _show_progress(self, indeterminate: bool, cancelable: bool = True) -> None:
        self.progress_bar.setRange(0, 0) if indeterminate else self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(True)
        self.cancel_button.setVisible(cancelable)

    def _hide_progress_if_idle(self) -> None:
        if self._thread is None and self._history_thread is None and self._export_thread is None:
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)

    def cancel_current_operation(self) -> None:
        if self._thread is not None:
            self._thread.requestInterruption()
            self.statusBar().showMessage("Cancelling import…")
        if self._export_thread is not None:
            self._export_thread.requestInterruption()
            self.statusBar().showMessage("Cancelling export…")

    def show_error(self, message: str) -> None:
        self.statusBar().showMessage("Could not load file")
        QMessageBox.warning(self, "Could not load file", message)

    def _load_progress(self, rows_read: int) -> None:
        if self._path is not None:
            self.statusBar().showMessage(
                f"Loading {self._path.name}… {rows_read:,} rows read"
            )

    def _load_cancelled(self) -> None:
        self.statusBar().showMessage("Import cancelled")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._workers_are_idle():
            event.accept()
            return

        event.ignore()
        if self._closing:
            return
        self._closing = True
        self._pending_reload = False
        self.setEnabled(False)
        self.statusBar().showMessage("Stopping background work before closing…")
        if self._thread is not None:
            self._thread.requestInterruption()
        if self._export_thread is not None:
            self._export_thread.requestInterruption()

    def _workers_are_idle(self) -> bool:
        return (
            self._thread is None
            and self._history_thread is None
            and self._export_thread is None
        )

    def _finish_close_if_idle(self) -> None:
        if self._closing and self._workers_are_idle():
            QTimer.singleShot(0, self.close)
