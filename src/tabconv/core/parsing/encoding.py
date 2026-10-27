from ..errors import InvalidEncodingError


def decode_bytes(data: bytes, requested: str | None = None) -> tuple[str, str]:
    if requested:
        try:
            return data.decode(requested), requested
        except (LookupError, UnicodeDecodeError) as error:
            raise InvalidEncodingError(f"Cannot decode input as {requested}") from error
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig"), "utf-8-sig"
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        try:
            from charset_normalizer import from_bytes
        except ImportError as error:
            raise InvalidEncodingError("Input is not UTF-8; install charset-normalizer or select encoding") from error
        match = from_bytes(data).best()
        if match is None or match.encoding is None:
            raise InvalidEncodingError("Could not detect input encoding")
        return str(match), match.encoding
