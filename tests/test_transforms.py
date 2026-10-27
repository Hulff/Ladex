import pytest

from tabconv.core.errors import InvalidTransformationError
from tabconv.core.history import DatasetHistory, operation_from_dict
from tabconv.core.models import Dataset
from tabconv.core.transforms import ConvertDecimalSeparator, RemoveColumns, ReplaceText


@pytest.fixture
def dataset() -> Dataset:
    return Dataset(
        ("amount", "label", "code"),
        (("11.214", "ALPHA", "001.2"), ("1245,3", "alpha", "text.1")),
    )


def test_replace_text_all_columns_case_insensitive(dataset: Dataset) -> None:
    result = ReplaceText("a", "x", case_sensitive=False).apply(dataset)
    assert result.rows == (("11.214", "xLPHx", "001.2"), ("1245,3", "xlphx", "text.1"))
    assert dataset.rows[0][1] == "ALPHA"


def test_replace_text_selected_columns(dataset: Dataset) -> None:
    result = ReplaceText(".", ",", columns=(0,)).apply(dataset)
    assert result.rows == (("11,214", "ALPHA", "001.2"), ("1245,3", "alpha", "text.1"))


def test_decimal_conversion_only_changes_numeric_values(dataset: Dataset) -> None:
    result = ConvertDecimalSeparator(".", ",").apply(dataset)
    assert result.rows == (("11,214", "ALPHA", "001,2"), ("1245,3", "alpha", "text.1"))


def test_decimal_conversion_honors_thousands_separator() -> None:
    source = Dataset(("amount",), (("1,234.50",), ("bad,12.50",)))
    result = ConvertDecimalSeparator(".", ",", thousands_separator=",").apply(source)
    assert result.rows == (("1234,50",), ("bad,12.50",))


def test_decimal_conversion_supports_scientific_notation_both_ways() -> None:
    source = Dataset(("amount",), (("9.64847E-2",), ("242.0",), ("9.14168E-2",)))
    comma = ConvertDecimalSeparator(".", ",").apply(source)
    assert comma.rows == (("9,64847E-2",), ("242,0",), ("9,14168E-2",))
    point = ConvertDecimalSeparator(",", ".").apply(comma)
    assert point.rows == source.rows


def test_remove_columns(dataset: Dataset) -> None:
    result = RemoveColumns((1,)).apply(dataset)
    assert result.columns == ("amount", "code")
    assert result.rows == (("11.214", "001.2"), ("1245,3", "text.1"))


def test_invalid_column_index_is_reported(dataset: Dataset) -> None:
    with pytest.raises(InvalidTransformationError):
        RemoveColumns((3,)).apply(dataset)


def test_history_undo_redo_reset_and_branching(dataset: Dataset) -> None:
    history = DatasetHistory(dataset)
    history.apply(ReplaceText("ALPHA", "BETA"))
    history.apply(RemoveColumns((2,)))
    assert history.current.columns == ("amount", "label")
    assert history.undo().columns == dataset.columns
    assert history.redo().columns == ("amount", "label")
    history.undo()
    history.apply(ReplaceText("11", "12", columns=(0,)))
    assert not history.can_redo
    assert history.current.rows[0][0] == "12.214"
    assert history.reset() == dataset
    assert not history.can_undo


def test_operation_serialization_round_trip(dataset: Dataset) -> None:
    history = DatasetHistory(dataset)
    history.apply(ReplaceText("ALPHA", "BETA", columns=(1,), case_sensitive=False))
    history.apply(ConvertDecimalSeparator(".", ","))
    serialized = history.serialize()
    restored = DatasetHistory(dataset)
    assert restored.load(serialized) == history.current
    assert operation_from_dict(serialized[0]).to_dict() == serialized[0]
