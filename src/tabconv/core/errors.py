class TabConvError(Exception):
    """Base class for expected conversion errors."""


class UnsupportedFormatError(TabConvError):
    pass


class InvalidEncodingError(TabConvError):
    pass


class MalformedQuotesError(TabConvError):
    pass


class InconsistentRowsError(TabConvError):
    def __init__(self, issues: list[tuple[int, int, int]]) -> None:
        self.issues = issues
        description = ", ".join(f"line {line}: expected {expected}, got {actual}" for line, expected, actual in issues)
        super().__init__(f"Inconsistent row widths: {description}")
