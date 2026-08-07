"""課題側から与えるOTの定数と補助関数です。編集しないでください。

OTの群は手計算・デバッグ用の極小パラメータです。総当たり可能なので、
暗号学的な安全性はありません。
"""

from __future__ import annotations

import hashlib

# F_23^*の位数11の部分群です。2^11 = 1 mod 23です。
OT_P = 23
OT_Q = 11
OT_G = 2


def validate_choice(choice: int) -> None:
    if choice not in (0, 1):
        raise ValueError("choice must be 0 or 1")


def validate_ot_scalar(value: int, name: str = "OT scalar") -> None:
    if not 1 <= value < OT_Q:
        raise ValueError(f"{name} must be in 1..{OT_Q - 1}")


def validate_group_element(value: int, name: str = "group element") -> None:
    if not 1 <= value < OT_P or pow(value, OT_Q, OT_P) != 1:
        raise ValueError(f"{name} is not in the order-{OT_Q} subgroup")


def derive_pad(shared: int, branch: int, length: int) -> bytes:
    """Hash a toy DH shared value into `length` bytes."""
    validate_group_element(shared, "shared value")
    validate_choice(branch)
    if length < 0:
        raise ValueError("length must be non-negative")

    seed = b"ac2026-toy-ot" + bytes([shared, branch])
    output = bytearray()
    counter = 0
    while len(output) < length:
        output.extend(hashlib.sha256(seed + counter.to_bytes(4, "big")).digest())
        counter += 1
    return bytes(output[:length])


def xor_bytes(left: bytes, right: bytes) -> bytes:
    if len(left) != len(right):
        raise ValueError("byte strings must have the same length")
    return bytes(x ^ y for x, y in zip(left, right))
