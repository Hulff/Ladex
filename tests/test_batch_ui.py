from pathlib import Path

from pytestqt.qtbot import QtBot

from tabconv.ui.main_window import MainWindow


def test_multi_file_open_and_shared_column_operations(
    qtbot: QtBot, tmp_path: Path
) -> None:
    first = tmp_path / "first.csv"
    first.write_text("amount,label\n1.25,alpha\n", encoding="utf-8")
    second = tmp_path / "second.csv"
    second.write_text("label,amount,extra\nbeta,2.50,z\n", encoding="utf-8")
    window = MainWindow()
    qtbot.addWidget(window)

    window.open_paths((first, second))
    qtbot.waitUntil(lambda: window._thread is None, timeout=5_000)

    assert window.file_tabs.count() == 2
    window.file_tabs.setCurrentIndex(1)
    window.operation_columns.setCurrentIndex(window.operation_columns.findData(1))
    window.find_text.setText(".")
    window.replacement_text.setText(",")
    window.replace_text()
    qtbot.waitUntil(lambda: window._history_thread is None, timeout=5_000)
    assert window.file_tabs.count() == 2
    assert window.file_tabs.currentIndex() == 1
    assert window._current_dataset is not None
    assert window._current_dataset[0].rows[0][0] == "1,25"
    assert window._current_dataset[1].rows[0][1] == "2,50"

    window.remove_columns.setCurrentIndex(1)
    window.remove_selected_column()
    qtbot.waitUntil(lambda: window._history_thread is None, timeout=5_000)
    assert window.file_tabs.count() == 2
    assert window.file_tabs.currentIndex() == 1
    assert window._current_dataset[0].columns == ("label",)
    assert window._current_dataset[1].columns == ("label", "extra")
