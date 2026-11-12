"""Minimal deterministic CBOR (RFC 8949) for Receipt-v1 maps.

Encodes ints, text, bytes, arrays, and maps. Map keys are sorted by encoded
length, then by encoded bytes. Indefinite lengths are rejected.
"""

from __future__ import annotations


def _head(major: int, length: int) -> bytes:
    if length < 24:
        return bytes([major | length])
    if length < 256:
        return bytes([major | 24, length])
    if length < 65536:
        return bytes([major | 25]) + length.to_bytes(2, "big")
    if length < 2**32:
        return bytes([major | 26]) + length.to_bytes(4, "big")
    return bytes([major | 27]) + length.to_bytes(8, "big")


def encode(value: object) -> bytes:
    if value is False:
        return b"\xf4"
    if value is True:
        return b"\xf5"
    if value is None:
        return b"\xf6"
    if isinstance(value, int) and not isinstance(value, bool):
        if value >= 0:
            return _head(0, value)
        return _head(0x20, -1 - value)
    if isinstance(value, bytes):
        return _head(0x40, len(value)) + value
    if isinstance(value, str):
        raw = value.encode("utf-8")
        return _head(0x60, len(raw)) + raw
    if isinstance(value, list):
        return _head(0x80, len(value)) + b"".join(encode(item) for item in value)
    if isinstance(value, dict):
        pairs: list[tuple[bytes, bytes]] = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("CBOR map keys must be text")
            pairs.append((encode(key), encode(item)))
        pairs.sort(key=lambda pair: (len(pair[0]), pair[0]))
        return _head(0xA0, len(pairs)) + b"".join(key + item for key, item in pairs)
    raise TypeError(f"unsupported CBOR value {type(value).__name__}")


def _read_length(buf: bytes, index: int, additional: int) -> tuple[int, int]:
    if additional < 24:
        return additional, index
    if additional == 24:
        return buf[index], index + 1
    if additional == 25:
        return int.from_bytes(buf[index:index + 2], "big"), index + 2
    if additional == 26:
        return int.from_bytes(buf[index:index + 4], "big"), index + 4
    if additional == 27:
        return int.from_bytes(buf[index:index + 8], "big"), index + 8
    raise ValueError("indefinite or reserved CBOR length")


def _decode_at(buf: bytes, index: int) -> tuple[object, int]:
    initial = buf[index]
    major = initial >> 5
    additional = initial & 0x1F
    index += 1
    if major == 0:
        return _read_length(buf, index, additional)
    if major == 1:
        number, index = _read_length(buf, index, additional)
        return -1 - number, index
    if major in (2, 3):
        length, index = _read_length(buf, index, additional)
        chunk = buf[index:index + length]
        index += length
        if major == 2:
            return chunk, index
        return chunk.decode("utf-8"), index
    if major == 4:
        length, index = _read_length(buf, index, additional)
        items: list[object] = []
        for _ in range(length):
            item, index = _decode_at(buf, index)
            items.append(item)
        return items, index
    if major == 5:
        length, index = _read_length(buf, index, additional)
        mapping: dict[object, object] = {}
        for _ in range(length):
            key, index = _decode_at(buf, index)
            item, index = _decode_at(buf, index)
            mapping[key] = item
        return mapping, index
    if major == 7 and additional == 20:
        return False, index
    if major == 7 and additional == 21:
        return True, index
    if major == 7 and additional == 22:
        return None, index
    raise ValueError(f"unsupported CBOR major {major}")


def decode(buf: bytes) -> object:
    value, index = _decode_at(buf, 0)
    if index != len(buf):
        raise ValueError("trailing bytes after CBOR value")
    return value
