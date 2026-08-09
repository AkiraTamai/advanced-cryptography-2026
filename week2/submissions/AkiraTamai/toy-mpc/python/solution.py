"""Week 2課題「toy-mpc」の解答ファイルです。

`NotImplementedError`のある8関数を実装してください。
`PROVIDED`と書かれた補助関数は、課題側から与える道具です。

このコードは教育用の集中シミュレータであり、実用上の安全性はありません。
"""

from __future__ import annotations

from given import (
    OT_G,
    OT_P,
    derive_pad,
    validate_choice,
    validate_group_element,
    validate_receiver_scalar,
    validate_sender_scalar,
    xor_bytes,
)

ShareVector = list[int]
BeaverTriple = tuple[ShareVector, ShareVector, ShareVector]


# ========================================================== PROVIDED helpers
def _validate_modulus(modulus: int) -> None:
    if modulus <= 1:
        raise ValueError("modulus must be greater than 1")


def _validate_same_share_count(*vectors: ShareVector) -> int:
    """Return the common party count, or raise ValueError."""
    if not vectors or len(vectors[0]) < 2:
        raise ValueError("a share vector must contain at least two parties")
    count = len(vectors[0])
    if any(len(vector) != count for vector in vectors):
        raise ValueError("share vectors must have the same number of parties")
    return count


def _validate_bit(value: int, name: str = "bit") -> None:
    if value not in (0, 1):
        raise ValueError(f"{name} must be 0 or 1")


def _validate_bit_shares(shares: tuple[int, int], name: str) -> None:
    if len(shares) != 2:
        raise ValueError(f"{name} must contain exactly two shares")
    _validate_bit(shares[0], f"{name}[0]")
    _validate_bit(shares[1], f"{name}[1]")


# ================================================================ Part A1
def share(secret: int, randomness: list[int], modulus: int) -> ShareVector:
    """Split `secret` into len(randomness) + 1 additive shares.

    The values in `randomness` are the first shares. Return canonical field
    elements in 0..modulus-1. At least two parties are required.
    """
    _validate_modulus(modulus)
    # 0..p-1 の正規形（canonical form) -> randomnessはp以上の値も負数も受け入れる
    normalized = [value % modulus for value in randomness]
    final = (secret - sum(normalized)) % modulus
    shares = normalized + [final]
    _validate_same_share_count(shares)
    return shares

def reconstruct(shares: ShareVector, modulus: int) -> int:
    """Open additive shares and return the canonical field element."""
    _validate_modulus(modulus)
    _validate_same_share_count(shares)
    return sum(shares) % modulus

# ================================================================ Part A2
def add_shares(
    left_shares: ShareVector,
    right_shares: ShareVector,
    modulus: int,
) -> ShareVector:
    """Add two shared values component-wise without opening them."""
    _validate_modulus(modulus)
    _validate_same_share_count(left_shares, right_shares)
    return [
        (left + right) % modulus
        for left, right in zip(left_shares, right_shares)
    ]

# ---------------------------------------------------------- PROVIDED helpers
def sub_shares(
    left_shares: ShareVector,
    right_shares: ShareVector,
    modulus: int,
) -> ShareVector:
    """Subtract two shared values component-wise. This is local."""
    _validate_modulus(modulus)
    _validate_same_share_count(left_shares, right_shares)
    return [
        (left - right) % modulus
        for left, right in zip(left_shares, right_shares)
    ]

def scale_shares(
    shares: ShareVector,
    scalar: int,
    modulus: int,
) -> ShareVector:
    """Multiply a shared value by a public scalar. This is local."""
    _validate_modulus(modulus)
    _validate_same_share_count(shares)
    return [(value * scalar) % modulus for value in shares]


# ================================================================ Part A3
def beaver_multiply(
    x_shares: ShareVector,
    y_shares: ShareVector,
    triple: BeaverTriple,
    modulus: int,
) -> ShareVector:
    """Return additive shares of x*y using one Beaver triple.

    If triple = ([a], [b], [c]) with c = a*b, open exactly

        d = x-a,  e = y-b
        x = d + a、y = e + b

    and compute

        [xy] = [c] + d[b] + e[a] + de.
        x*y = (d+a)(e+b) = d*e + d*b + e*a + a*b = d*e + d*b + e*a + c

    Add the public term d*e to party 0 only.
    """
    _validate_modulus(modulus)
    a_shares, b_shares, c_shares = triple
    _validate_same_share_count(
        x_shares,
        y_shares,
        a_shares,
        b_shares,
        c_shares,
    )

    # [d] = [x] - [a]
    d_shares = sub_shares(x_shares, a_shares, modulus)
    # [e] = [y] - [b]
    e_shares = sub_shares(y_shares, b_shares, modulus)

    # round 2 -> 公開するのはdとeのみ
    # 総和 mod p -> d = x - a
    d = reconstruct(d_shares, modulus)
    # 総和 mod p -> e = y - b
    e = reconstruct(e_shares, modulus)

    # 導出: x*y = (d+a)(e+b) = d*e + d*b + e*a + a*b = d*e + d*b + e*a + c
    # c_i = a*bのshare, d * b_i(総和するとd*b), e * a_i(総和するとe*a)
    # コメント「Add the public term d*e to party 0 only」 -> (d * e if index == 0 else 0) 公開値の定数(d*e) ≠ (n * d*e)のため
    return [
        (c_i + d * b_i + e * a_i + (d * e if index == 0 else 0)) % modulus
        for index, (a_i, b_i, c_i) in enumerate(
            zip(a_shares, b_shares, c_shares)
        )
    ]

# ========================================================== PROVIDED XOR MPC
def xor_share(bit: int, mask: int) -> tuple[int, int]:
    """Split a bit into two XOR shares: bit = mask XOR (bit XOR mask)."""
    _validate_bit(bit, "bit")
    _validate_bit(mask, "mask")
    return mask, bit ^ mask


def xor_reconstruct(shares: tuple[int, int]) -> int:
    """Open two XOR shares."""
    _validate_bit_shares(shares, "shares")
    return shares[0] ^ shares[1]


def xor_shares(
    left_shares: tuple[int, int],
    right_shares: tuple[int, int],
) -> tuple[int, int]:
    """XOR two XOR-shared bits locally."""
    _validate_bit_shares(left_shares, "left_shares")
    _validate_bit_shares(right_shares, "right_shares")
    return (
        left_shares[0] ^ right_shares[0],
        left_shares[1] ^ right_shares[1],
    )


# ========================================================== PROVIDED OT setup
def ot_sender_setup(sender_secret: int) -> int:
    """Return A = g^a mod p for sender secret a."""
    validate_sender_scalar(sender_secret, "sender_secret")
    return pow(OT_G, sender_secret, OT_P)


# ================================================================ Part B1
def ot_receiver_request(
    sender_public: int,
    choice: int,
    receiver_secret: int,
) -> int:
    """Build receiver request B.

    B = g^b for choice 0, and B = A*g^b for choice 1.
    The receiver secret b is sampled from 0..q-1, including zero.
    """
    # check (1 <= A < 23 かつ A^11 ≡ 1 (mod 23))?
    validate_group_element(sender_public, "sender_public")

    # check choiceが0か1か
    # {g^b : b=0..10}, {A·g^b : b=0..10} -> 同じ部分群全体。choiceに寄らずBの分布が一様
    validate_choice(choice)

    # check bは0..10の範囲か
    validate_receiver_scalar(receiver_secret, "receiver_secret")

    # g^b mod p
    blinded = pow(OT_G, receiver_secret, OT_P)

    if choice == 0:
        # B = g^b mod p
        return blinded
        # B = (A · g^b) mod p
    return sender_public * blinded % OT_P

# 1-out-of-2 OTの送信者側暗号化関数
def ot_sender_encrypt(
    sender_secret: int,
    request: int,
    message_0: bytes,
    message_1: bytes,
) -> tuple[bytes, bytes]:
    """Encrypt two equal-length messages for the 1-out-of-2 OT.

    Derive the branch-0 key from B^a and the branch-1 key from (B/A)^a.
    Use derive_pad(shared, branch, length), then xor_bytes(message, pad).
    """

    # check 1 <= a < 11（1..10
    validate_sender_scalar(sender_secret, "sender_secret")

    # check Bが位数11の部分群の元でなければerror -> (1 <= B < 23 かつ B^11 mod 23 == 1)
    validate_group_element(request, "request")

    #  2つのメッセージ長が同じでなければ、XORパッドの長さが合わなくなるのでエラー
    if len(message_0) != len(message_1):
        raise ValueError("messages must have the same length")

    # A = g^a mod p
    sender_public = ot_sender_setup(sender_secret)

    # branch-0の「B^a mod p」
    shared_0 = pow(request, sender_secret, OT_P)

    # Aの逆元である「A^{-1} mod 23」
    inverse = pow(sender_public, -1, OT_P)

    # B * A^{-1} = B/A mod p -> (B/A)^a mod p
    shared_1 = pow(request * inverse % OT_P, sender_secret, OT_P)

    # shared_0とbranch-0、len(message_0) からパッド(擬似乱数バイト列)を作り(derive_pad)、平文message_0をXOR暗号化(xor_bytes)
    ciphertext_0 = xor_bytes(
        message_0,
        derive_pad(shared_0, 0, len(message_0)),
    )
    # shared_1とbranch-1、len(message_1) からパッド(擬似乱数バイト列)を作り、平文message_0をXOR暗号化
    ciphertext_1 = xor_bytes(
        message_1,
        derive_pad(shared_1, 1, len(message_1)),
    )
    return ciphertext_0, ciphertext_1

# 1-out-of-2 OTの受信者側復号関数
def ot_receiver_decrypt(
    sender_public: int,
    choice: int,
    receiver_secret: int,
    ciphertexts: tuple[bytes, bytes],
) -> bytes:
    """Decrypt the selected OT ciphertext using A^b."""
    validate_group_element(sender_public, "sender_public")
    validate_choice(choice)
    validate_receiver_scalar(receiver_secret, "receiver_secret")
    if len(ciphertexts) != 2:
        raise ValueError("ciphertexts must contain exactly two messages")
    selected = ciphertexts[choice]

    # A^b mod p -> A^b = (g^a)^b = g^{a·b} = g^{ab} -> A^b mod p = g^{ab} mod p
    # ex. if a = 5、b = 3の場合、
    # A = g^a = 2^5 mod 23 = 32 mod 23 = 9
    # shared = A^b = 9^3 mod 23 = 729 mod 23 = 16
    # g^{ab} = 2^{15} mod 23 = 32768 mod 23 = 16
    shared = pow(sender_public, receiver_secret, OT_P)

    # sharedとどちらのbranchをchoice、len(selected)からパッド(擬似乱数バイト列)を生成(送信者側のpadを再現)
    pad = derive_pad(shared, choice, len(selected))

    # ciphertextと同じパッド padで再度XORして平文に戻す
    # 例
    # ciphertext = 平文 XOR pad
    # 平文    = ciphertext XOR pad
    return xor_bytes(selected, pad)

# ---------------------------------------------------------- PROVIDED OT glue
def _ot_transfer_bit(
    message_0: int,
    message_1: int,
    choice: int,
    sender_secret: int,
    receiver_secret: int,
) -> int:
    """Run the student OT functions for a one-bit message."""
    _validate_bit(message_0, "message_0")
    _validate_bit(message_1, "message_1")
    validate_choice(choice)

    sender_public = ot_sender_setup(sender_secret)
    request = ot_receiver_request(sender_public, choice, receiver_secret)
    ciphertexts = ot_sender_encrypt(
        sender_secret,
        request,
        bytes([message_0]),
        bytes([message_1]),
    )
    plaintext = ot_receiver_decrypt(
        sender_public,
        choice,
        receiver_secret,
        ciphertexts,
    )
    if len(plaintext) != 1 or plaintext[0] not in (0, 1):
        raise ValueError("bit OT must return one byte equal to 0 or 1")
    return plaintext[0]


# ================================================================ Part B2
def gmw_and(
    x_shares: tuple[int, int],
    y_shares: tuple[int, int],
    masks: tuple[int, int],
    ot_secrets: tuple[tuple[int, int], tuple[int, int]],
) -> tuple[int, int]:
    """AND two XOR-shared bits using two 1-out-of-2 OTs.

    x_shares = (x0, x1), y_shares = (y0, y1)
    masks = (r01, r10)

    Session 01: P0 sends (r01, r01 XOR x0), P1 chooses y1.
    Session 10: P1 sends (r10, r10 XOR x1), P0 chooses y0.

    `ot_secrets` contains (sender_secret, receiver_secret) for session 01 and
    session 10, in that order.
    """
    raise NotImplementedError
