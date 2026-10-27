from pathlib import Path

from tabconv.core.batch import BatchHistory
from tabconv.core.models import Dataset
from tabconv.core.transforms import ConvertDecimalSeparator, RemoveColumns, ReplaceText


def test_batch_corrections_match_column_names_across_different_schemas() -> None:
    first = Dataset(
        ("amount", "label"),
        (("1.25", "alpha"),),
        Path("first.csv"),
    )
    second = Dataset(
        ("label", "amount", "amount"),
        (("beta", "2.50", "3.75"), ("gamma", "4.00", "5.25")),
        Path("second.csv"),
    )
    history = BatchHistory((first, second))

    result = history.apply(ConvertDecimalSeparator(".", ","), ("amount",))

    assert result[0].rows == (("1,25", "alpha"),)
    assert result[1].rows == (("beta", "2,50", "3,75"), ("gamma", "4,00", "5,25"))
    assert result[1].row_count == 2

    result = history.apply(ReplaceText("a", "x"), ("label",))
    assert result[0].rows == (("1,25", "xlphx"),)
    assert result[1].rows == (("betx", "2,50", "3,75"), ("gxmmx", "4,00", "5,25"))


def test_batch_deletion_removes_name_from_every_file_and_history_can_undo() -> None:
    first = Dataset(("drop", "keep"), (("x", "1"),), Path("first.csv"))
    second = Dataset(
        ("keep", "drop", "drop"), (("2", "y", "z"),), Path("second.csv")
    )
    history = BatchHistory((first, second))

    removed = history.apply(RemoveColumns((0,)), ("drop",))
    assert removed[0].columns == ("keep",)
    assert removed[1].columns == ("keep",)
    assert removed[1].rows == (("2",),)
    assert history.undo() == (first, second)
    assert history.redo() == removed
    assert history.reset() == (first, second)
