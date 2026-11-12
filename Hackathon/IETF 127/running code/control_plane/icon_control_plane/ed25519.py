"""Ed25519 sign and verify (RFC 8032). Standard library only.

Not constant-time. A bad signature collapses the gate. This module does not
target a side-channel adversary sharing the CPU.
"""

from __future__ import annotations

import hashlib

P = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D_CURVE = (-121665 * pow(121666, P - 2, P)) % P
I_SQRT = pow(2, (P - 1) // 4, P)
_BX = 15112221349535400772501151409588531511454012693041857206046113283949847762202
_BY = 46316835694926478169428394003475163141307993866256225615783033603165251855960
_IDENTITY = (0, 1, 1, 0)
_BASE = (_BX, _BY, 1, (_BX * _BY) % P)


def _add(point_a: tuple[int, int, int, int], point_b: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x1, y1, z1, t1 = point_a
    x2, y2, z2, t2 = point_b
    a = ((y1 - x1) * (y2 - x2)) % P
    b = ((y1 + x1) * (y2 + x2)) % P
    c = (2 * t1 * t2 * D_CURVE) % P
    d2 = (2 * z1 * z2) % P
    e = b - a
    f = d2 - c
    g = d2 + c
    h = b + a
    return ((e * f) % P, (g * h) % P, (f * g) % P, (e * h) % P)


def _scalarmult(scalar: int, point: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    if scalar == 0:
        return _IDENTITY
    table = [_IDENTITY, point]
    for _ in range(2, 16):
        table.append(_add(table[-1], point))
    nibbles: list[int] = []
    value = scalar
    while value:
        nibbles.append(value & 0xF)
        value >>= 4
    acc = _IDENTITY
    for nib in reversed(nibbles):
        acc = _add(acc, acc)
        acc = _add(acc, acc)
        acc = _add(acc, acc)
        acc = _add(acc, acc)
        if nib:
            acc = _add(acc, table[nib])
    return acc


def _encode_point(point: tuple[int, int, int, int]) -> bytes:
    x, y, z, _t = point
    inv_z = pow(z, P - 2, P)
    x = (x * inv_z) % P
    y = (y * inv_z) % P
    raw = bytearray(y.to_bytes(32, "little"))
    if x & 1:
        raw[31] |= 0x80
    return bytes(raw)


def _recover_x(y: int, sign: int) -> int | None:
    if y >= P:
        return None
    y2 = (y * y) % P
    x2 = ((y2 - 1) * pow((D_CURVE * y2 + 1) % P, P - 2, P)) % P
    if x2 == 0:
        if sign:
            return None
        return 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P != 0:
        x = (x * I_SQRT) % P
    if (x * x - x2) % P != 0:
        return None
    if (x & 1) != sign:
        x = P - x
    return x


def _decode_point(raw: bytes) -> tuple[int, int, int, int] | None:
    if len(raw) != 32:
        return None
    y = int.from_bytes(raw, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, (x * y) % P)


def _expand_seed(seed: bytes) -> tuple[int, bytes]:
    if len(seed) != 32:
        raise ValueError("Ed25519 seed must be 32 bytes")
    digest = hashlib.sha512(seed).digest()
    clamped = bytearray(digest[:32])
    clamped[0] &= 248
    clamped[31] &= 63
    clamped[31] |= 64
    return int.from_bytes(clamped, "little"), digest[32:]


def public_key(seed: bytes) -> bytes:
    scalar, _prefix = _expand_seed(seed)
    return _encode_point(_scalarmult(scalar, _BASE))


def sign(seed: bytes, message: bytes) -> bytes:
    scalar, prefix = _expand_seed(seed)
    public = _encode_point(_scalarmult(scalar, _BASE))
    nonce = int.from_bytes(hashlib.sha512(prefix + message).digest(), "little") % L
    commitment = _encode_point(_scalarmult(nonce, _BASE))
    challenge = int.from_bytes(hashlib.sha512(commitment + public + message).digest(), "little") % L
    signature_s = (nonce + challenge * scalar) % L
    return commitment + signature_s.to_bytes(32, "little")


def verify(public: bytes, message: bytes, signature: bytes) -> bool:
    if len(public) != 32 or len(signature) != 64:
        return False
    commitment = signature[:32]
    signature_s = int.from_bytes(signature[32:], "little")
    if signature_s >= L:
        return False
    point_a = _decode_point(public)
    point_r = _decode_point(commitment)
    if point_a is None or point_r is None:
        return False
    challenge = int.from_bytes(hashlib.sha512(commitment + public + message).digest(), "little") % L
    left = _scalarmult(signature_s, _BASE)
    right = _add(point_r, _scalarmult(challenge, point_a))
    return _encode_point(left) == _encode_point(right)
