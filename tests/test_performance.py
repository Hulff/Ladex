from time import perf_counter

import pytest

from tabconv.core.models import ImportOptions
from tabconv.core.parsing.reader import parse_text


@pytest.mark.slow
def test_import_100k_rows_reports_elapsed_time() -> None:
    source = "name,value\n" + "item,123.45\n" * 100_000
    started = perf_counter()
    dataset = parse_text(source, ImportOptions(delimiter=","))
    elapsed = perf_counter() - started
    assert dataset.row_count == 100_000
    print(f"Parsed 100,000 rows in {elapsed:.3f}s")
