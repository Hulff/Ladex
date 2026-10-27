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
    app.setStyleSheet(_catppuccin_mocha_stylesheet())
    icon_path = Path(__file__).resolve().parents[3] / "icon" / "favicon.ico"
    if getattr(sys, "_MEIPASS", None):
        icon_path = Path(sys._MEIPASS) / "favicon.ico"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    if "--smoke-test" in sys.argv:
        window.close()
        return 0
    window.show()
    return app.exec()


def _catppuccin_mocha_stylesheet() -> str:
    return """
    QWidget { background-color: #1e1e2e; color: #cdd6f4; }
    QMainWindow, QDialog, QMenuBar, QMenu, QStatusBar { background-color: #181825; }
    QFrame { border-color: #45475a; }
    QPushButton, QComboBox, QLineEdit, QListWidget, QTableView, QTabWidget::pane {
        background-color: #313244; color: #cdd6f4; border: 1px solid #45475a;
        border-radius: 5px; padding: 5px;
    }
    QPushButton:hover, QComboBox:hover { background-color: #45475a; }
    QPushButton:pressed { background-color: #585b70; }
    QPushButton:disabled { color: #6c7086; background-color: #181825; }
    QComboBox QAbstractItemView { background-color: #313244; selection-background-color: #585b70; }
    QCheckBox::indicator { width: 15px; height: 15px; }
    QCheckBox::indicator:unchecked { background: #313244; border: 1px solid #6c7086; }
    QCheckBox::indicator:checked { background: #cba6f7; border: 1px solid #cba6f7; }
    QHeaderView::section { background-color: #181825; color: #cdd6f4; padding: 5px; border: 1px solid #45475a; }
    QTableView { alternate-background-color: #242436; gridline-color: #45475a; }
    QTableView::item:selected { background-color: #585b70; color: #cdd6f4; }
    QTabBar::tab { background: #313244; color: #bac2de; padding: 7px 10px; border: 1px solid #45475a; }
    QTabBar::tab:selected { background: #45475a; color: #cdd6f4; }
    QProgressBar { background: #313244; border: 1px solid #45475a; border-radius: 4px; text-align: center; }
    QProgressBar::chunk { background-color: #cba6f7; }
    QScrollBar:vertical { background: #181825; width: 12px; }
    QScrollBar::handle:vertical { background: #585b70; min-height: 24px; border-radius: 5px; }
    QToolTip { background: #313244; color: #cdd6f4; border: 1px solid #cba6f7; }
    """


if __name__ == "__main__":
    raise SystemExit(main())
