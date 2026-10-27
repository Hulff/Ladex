from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Ladex")
    app.setStyle("Fusion")
    app.setStyleSheet(_dark_blue_stylesheet())
    icon_path = Path(__file__).resolve().parents[3] / "icon" / "favicon.ico"
    if getattr(sys, "_MEIPASS", None):
        icon_path = Path(sys._MEIPASS) / "favicon.ico"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    if icon_path.is_file():
        window.setWindowIcon(QIcon(str(icon_path)))
    if "--smoke-test" in sys.argv:
        window.close()
        return 0
    window.show()
    return app.exec()


def _dark_blue_stylesheet() -> str:
    return """
    QWidget { background-color: #17212b; color: #e6f1ff; }
    QMainWindow, QDialog, QMenuBar, QMenu, QStatusBar { background-color: #111a24; }
    QFrame { border-color: #2c3e50; }
    QPushButton, QComboBox, QLineEdit, QListWidget, QTableView, QTabWidget::pane {
        background-color: #203247; color: #e6f1ff; border: 1px solid #35516e;
        border-radius: 5px; padding: 5px;
    }
    QPushButton:hover, QComboBox:hover { background-color: #294461; }
    QPushButton:pressed { background-color: #35628b; }
    QPushButton:disabled { color: #718096; background-color: #111a24; }
    QComboBox QAbstractItemView { background-color: #203247; selection-background-color: #35628b; }
    QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; }
    QCheckBox::indicator:unchecked { background: #17212b; border: 2px solid #7193b5; }
    QCheckBox::indicator:checked { background: #3b82c4; border: 2px solid #63a8ed; }
    QCheckBox::indicator:checked:hover { background: #5599d5; }
    QHeaderView::section { background-color: #111a24; color: #e6f1ff; padding: 5px; border: 1px solid #35516e; }
    QTableView { alternate-background-color: #1b2938; gridline-color: #35516e; }
    QTableView::item:selected { background-color: #35628b; color: #ffffff; }
    QTabBar::tab { background: #203247; color: #b9cee3; padding: 7px 10px; border: 1px solid #35516e; }
    QTabBar::tab:selected { background: #294461; color: #ffffff; }
    QProgressBar { background: #203247; border: 1px solid #35516e; border-radius: 4px; text-align: center; }
    QProgressBar::chunk { background-color: #3b82c4; }
    QScrollBar:vertical { background: #111a24; width: 12px; }
    QScrollBar::handle:vertical { background: #35628b; min-height: 24px; border-radius: 5px; }
    QToolTip { background: #203247; color: #e6f1ff; border: 1px solid #63a8ed; }
    """


if __name__ == "__main__":
    raise SystemExit(main())
