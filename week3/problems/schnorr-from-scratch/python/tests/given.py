"""この課題で「与えられた道具」をまとめたファイルです。編集しないでください。

solution.py からは `from given import ...` で使えます。

- Curve / Point: 楕円曲線と点の表現
- TOY / SECP256K1: この課題で使う 2 本の曲線
- extended_gcd: 拡張ユークリッドの互除法(Part 1 の逆元で使います)
- is_on_curve: 点が曲線上にあるかのチェック(Part 2 のデバッグに便利です)
- challenge_hash: Fiat-Shamir 変換で使うハッシュ(Part 3 で使います)
"""

from __future__ import annotations

import hashlib
from typing import NamedTuple, Optional, Tuple

# 楕円曲線上の点は (x, y) のタプルで、無限遠点は None で表します。
Point = Optional[Tuple[int, int]]

# 無限遠点(群の単位元)です。solution.py でもこの値を使ってください。
INFINITY: Point = None


class Curve(NamedTuple):
    """短 Weierstrass 形の楕円曲線 y^2 = x^3 + a*x + b over F_p です。

    G は生成点(ベースポイント)、n は G の位数で、この課題では常に素数です。
    スカラーの計算は mod n、座標の計算は mod p で行う点に注意してください。
    """

    p: int              # 座標が住む素体 F_p の素数
    a: int              # 曲線の係数 a
    b: int              # 曲線の係数 b
    G: Tuple[int, int]  # 生成点
    n: int              # G の位数(素数)


# 手計算・デバッグ用の小さな曲線 y^2 = x^3 + 11 over F_1009 です。
# 群の位数 967 は素数なので、無限遠点以外のどの点も生成点になれます。
TOY = Curve(p=1009, a=0, b=11, G=(1, 298), n=967)

# Bitcoin などで実際に使われている曲線 secp256k1(y^2 = x^3 + 7)です。
SECP256K1 = Curve(
    p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
    a=0,
    b=7,
    G=(
        0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
        0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
    ),
    n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141,
)


def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """拡張ユークリッドの互除法です。

    (g, x, y) を返します。g は gcd(a, b) で、a*x + b*y == g が成り立ちます。

    たとえば extended_gcd(3, 11) は (1, 4, -1) を返します
    (3*4 + 11*(-1) == 1)。g == 1 のとき、x が「a の mod b での逆元」の
    候補になります。負のことがあるので、使うときは mod を取り直して
    ください。
    """
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    return old_r, old_s, old_t


def is_on_curve(P: Point, curve: Curve) -> bool:
    """P が曲線 y^2 = x^3 + a*x + b の上にあるかを調べます。無限遠点は True です。

    ec_add や ec_scalar_mul のデバッグに使ってください。実装が正しければ、
    曲線上の点どうしの計算結果は必ず曲線上に乗ります。乗らないときは
    公式のどこか(たいていは y_R の符号)が間違っています。
    """
    if P is None:
        return True
    x, y = P
    return (y * y - (x * x * x + curve.a * x + curve.b)) % curve.p == 0


def point_to_bytes(P: Point) -> bytes:
    """点を 64 バイトの固定長にエンコードします(ハッシュの入力用)。"""
    if P is None:
        return b"\x00" * 64
    x, y = P
    return x.to_bytes(32, "big") + y.to_bytes(32, "big")


def challenge_hash(R: Point, pubkey: Point, message: bytes, n: int) -> int:
    """Fiat-Shamir 変換のチャレンジ e = H(R || pubkey || message) mod n です。

    シグマプロトコルでは検証者がランダムに選んでいたチャレンジを、
    このハッシュ値で置き換えると署名方式になります(Part 3 参照)。
    """
    h = hashlib.sha256(
        point_to_bytes(R) + point_to_bytes(pubkey) + message
    ).digest()
    return int.from_bytes(h, "big") % n
