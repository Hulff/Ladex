import csv

from .whitespace import tokenize_whitespace


def detect_delimiter(lines: list[str]) -> str:
    """Return a delimiter, or raise when sampled rows make the choice unsafe."""
    nonempty = [line for line in lines if line.strip()][:20]
    if not nonempty:
        return "whitespace"
    scores: dict[str, int] = {}
    for candidate in (",", "\t", ";"):
        try:
            widths = [_csv_width(line, candidate) for line in nonempty]
        except csv.Error:
            continue
        if min(widths) > 1 and len(set(widths)) == 1:
            scores[candidate] = widths[0]
    # Tabular files with padded fields can also look whitespace-delimited. Prefer a
    # consistent explicit separator in that case to preserve each field's contents.
    if scores:
        if len(scores) == 1:
            return next(iter(scores))
        from ..errors import UnsupportedFormatError

        raise UnsupportedFormatError(
            "Delimiter detection is ambiguous; select a delimiter manually"
        )
    ws_widths = [len(tokenize_whitespace(line)) for line in nonempty]
    if min(ws_widths) > 1 and len(set(ws_widths)) == 1:
        return "whitespace"
    from ..errors import UnsupportedFormatError

    raise UnsupportedFormatError("Delimiter detection is ambiguous; select a delimiter manually")


def _csv_width(line: str, delimiter: str) -> int:
    return len(next(csv.reader([line], delimiter=delimiter, strict=True)))
