import argparse
from pathlib import Path

from .core.errors import TabConvError
from .core.models import ImportOptions
from .core.parsing.reader import read_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a tabular text file offline")
    parser.add_argument("input", type=Path)
    parser.add_argument("--delimiter", choices=[",", ";", "\\t", "whitespace"])
    parser.add_argument("--encoding")
    parser.add_argument("--no-header", action="store_true")
    args = parser.parse_args(argv)
    delimiter = "\t" if args.delimiter == "\\t" else args.delimiter
    try:
        dataset = read_file(args.input, ImportOptions(delimiter, args.encoding, not args.no_header))
    except (OSError, TabConvError) as error:
        parser.error(str(error))
    print(f"{dataset.row_count} rows × {dataset.column_count} columns")
    print(" | ".join(dataset.columns))
    return 0
