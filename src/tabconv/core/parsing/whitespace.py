from ..errors import MalformedQuotesError


def tokenize_whitespace(line: str) -> list[str]:
    """Split on runs of spaces/tabs outside CSV-style quoted fields."""
    fields: list[str] = []
    current: list[str] = []
    quoted = False
    at_boundary = True
    index = 0
    while index < len(line):
        char = line[index]
        if char == '"':
            if quoted and index + 1 < len(line) and line[index + 1] == '"':
                current.append('"')
                index += 2
                continue
            quoted = not quoted
            at_boundary = False
        elif not quoted and char in " \t":
            if not at_boundary:
                fields.append("".join(current))
                current = []
                at_boundary = True
        else:
            current.append(char)
            at_boundary = False
        index += 1
    if quoted:
        raise MalformedQuotesError("Unclosed quote in whitespace-delimited input")
    if not at_boundary:
        fields.append("".join(current))
    return fields
