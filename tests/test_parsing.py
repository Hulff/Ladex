from pathlib import Path

import pytest

from tabconv.core.errors import InconsistentRowsError, MalformedQuotesError, UnsupportedFormatError
from tabconv.core.models import ImportOptions
from tabconv.core.parsing.reader import parse_text, read_file
from tabconv.core.parsing.whitespace import tokenize_whitespace

EXAMPLE = '"collum 1" "col2"\n11.214     1245,3\n12.415     2256,7\n'


def test_guide_example_with_quoted_header_and_spaces() -> None:
    data = parse_text(EXAMPLE, ImportOptions(delimiter="whitespace"))
    assert data.columns == ("collum 1", "col2")
    assert data.rows == (("11.214", "1245,3"), ("12.415", "2256,7"))


@pytest.mark.parametrize("filename", ["CuComerc.txt", "CuComercUltrSo.txt"])
def test_example_tab_files_auto_detect_without_losing_padding(filename: str) -> None:
    path = Path(__file__).parents[1] / "test_files" / filename
    data = read_file(path)
    assert data.column_count == 3
    assert data.row_count == 911
    assert data.columns == ("Wavelength (nm)", "Absorbance (AU)", "Std.Dev.")
    assert data.rows[0][0] == "     190.0"


def test_whitespace_tabs_and_quoted_values() -> None:
    assert tokenize_whitespace('one\t  "two words"    three') == ["one", "two words", "three"]


@pytest.mark.parametrize("ending", ["\n", "\r\n"])
def test_csv_line_endings(ending: str) -> None:
    data = parse_text(f'a,b{ending}1,"two words"{ending}', ImportOptions(delimiter=","))
    assert data.rows == (("1", "two words"),)


def test_no_header_creates_names() -> None:
    data = parse_text("1,2\n3,4\n", ImportOptions(delimiter=",", has_header=False))
    assert data.columns == ("Column 1", "Column 2")
    assert data.rows[0] == ("1", "2")


def test_empty_file() -> None:
    assert parse_text("", ImportOptions(delimiter=",")).rows == ()


def test_empty_csv_cells_are_preserved() -> None:
    data = parse_text("a,b,c\n1,,3\n", ImportOptions(delimiter=","))
    assert data.rows == (("1", "", "3"),)


def test_inconsistent_rows_are_reported() -> None:
    with pytest.raises(InconsistentRowsError) as caught:
        parse_text("a,b\n1,2,3\n", ImportOptions(delimiter=","))
    assert caught.value.issues == [(2, 2, 3)]


def test_inconsistent_rows_can_be_padded() -> None:
    data = parse_text("name,value\nshort\nwide,2,extra\n", ImportOptions(delimiter=",", inconsistent_rows="pad"))
    assert data.columns == ("name", "value", "Column 3")
    assert data.rows == (("short", "", ""), ("wide", "2", "extra"))


def test_inconsistent_rows_can_be_truncated() -> None:
    data = parse_text("name,value\nshort\nwide,2,extra\n", ImportOptions(delimiter=",", inconsistent_rows="truncate"))
    assert data.columns == ("name", "value")
    assert data.rows == (("short",), ("wide", "2"))


def test_unclosed_quote_is_reported() -> None:
    with pytest.raises(MalformedQuotesError):
        tokenize_whitespace('one "two')


def test_malformed_csv_quote_is_reported() -> None:
    with pytest.raises(MalformedQuotesError):
        parse_text('a,b\n1,"two\n', ImportOptions(delimiter=","))


def test_ambiguous_delimiter_requires_choice() -> None:
    with pytest.raises(UnsupportedFormatError):
        parse_text("one\ntwo\n")


def test_utf8_bom_file(tmp_path: Path) -> None:
    source = tmp_path / "table.csv"
    source.write_bytes(b"\xef\xbb\xbfa,b\n1,2\n")
    data = read_file(source, ImportOptions(delimiter=","))
    assert data.columns == ("a", "b")


def test_unsupported_extension(tmp_path: Path) -> None:
    source = tmp_path / "table.xlsx"
    source.write_text("anything")
    with pytest.raises(UnsupportedFormatError):
        read_file(source)
