"""採点テストです。ローカルでは次のコマンドで実行します。

    bash scripts/test-python-submission.sh week3 schnorr-from-scratch <github-username>

期待値(テストベクトル)は出題側のリファレンス実装で生成したものです。
"""

from __future__ import annotations

import unittest

import solution
from given import INFINITY, SECP256K1, TOY, challenge_hash, is_on_curve


# ---------------------------------------------------------------- Part 1
class Part1Field(unittest.TestCase):
    """Part 1: F_p の足し算・掛け算・逆元のテストです。"""

    def test_add_basic(self) -> None:
        self.assertEqual(solution.field_add(3, 4, 7), 0)
        self.assertEqual(solution.field_add(10, 20, 17), 13)
        self.assertEqual(solution.field_add(0, 0, 5), 0)

    def test_add_normalizes(self) -> None:
        """範囲外の入力(負や p 以上)でも、結果が 0..p-1 に正規化されることを確認します。"""
        self.assertEqual(solution.field_add(-3, 1, 7), 5)
        self.assertEqual(solution.field_add(100, 100, 7), 200 % 7)

    def test_mul_basic(self) -> None:
        self.assertEqual(solution.field_mul(3, 4, 7), 5)
        self.assertEqual(solution.field_mul(0, 9, 11), 0)
        self.assertEqual(solution.field_mul(-2, 5, 13), (-10) % 13)

    def test_mul_large_prime(self) -> None:
        p = SECP256K1.p
        a = 0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF
        b = 0xFEDCBA9876543210FEDCBA9876543210FEDCBA9876543210
        self.assertEqual(solution.field_mul(a, b, p), (a * b) % p)

    def test_inv_small(self) -> None:
        for a, p in [(1, 7), (3, 11), (10, 17), (2, 1009), (966, 1009)]:
            with self.subTest(a=a, p=p):
                x = solution.field_inv(a, p)
                self.assertTrue(
                    0 <= x < p, "逆元は 0..p-1 に正規化して返してください"
                )
                self.assertEqual((a * x) % p, 1)

    def test_inv_negative_input(self) -> None:
        """ec_add の傾きの計算では、負の値の逆元も必要になります。"""
        p = 1009
        x = solution.field_inv(-5, p)
        self.assertEqual((-5 * x) % p, 1)

    def test_inv_large_prime(self) -> None:
        p = SECP256K1.p
        a = 0xDEADBEEF
        x = solution.field_inv(a, p)
        self.assertEqual((a * x) % p, 1)

    def test_inv_of_zero_raises(self) -> None:
        for a, p in [(0, 7), (7, 7), (2018, 1009)]:
            with self.subTest(a=a, p=p):
                with self.assertRaises(
                    ValueError,
                    msg="F_p で 0 の逆元は存在しないので ValueError を送出してください",
                ):
                    solution.field_inv(a, p)


# ---------------------------------------------------------------- Part 2
# クラス名の A/B は、テストの実行順(アルファベット順)を学習順に揃える
# ためのものです。
class Part2AToyCurve(unittest.TestCase):
    """Part 2 前半: 小さい曲線 y^2 = x^3 + 11 over F_1009 での群演算のテストです。"""

    def test_identity(self) -> None:
        G = TOY.G
        self.assertEqual(solution.ec_add(INFINITY, G, TOY), G)
        self.assertEqual(solution.ec_add(G, INFINITY, TOY), G)
        self.assertEqual(solution.ec_add(INFINITY, INFINITY, TOY), INFINITY)

    def test_inverse_points(self) -> None:
        """P + (-P) は無限遠点になります。-P は (x, -y) です。"""
        x, y = TOY.G
        minus_G = (x, (-y) % TOY.p)
        self.assertEqual(solution.ec_add(TOY.G, minus_G, TOY), INFINITY)

    def test_doubling(self) -> None:
        R = solution.ec_add(TOY.G, TOY.G, TOY)
        self.assertTrue(
            is_on_curve(R, TOY),
            f"2G = {R} が曲線上にありません。y_R = lam * (x_P - x_R) - y_P の"
            "符号や mod の取り忘れを確認してください",
        )
        self.assertEqual(R, (818, 800))

    def test_chord_addition(self) -> None:
        G2 = (818, 800)  # 2G
        R = solution.ec_add(TOY.G, G2, TOY)
        self.assertTrue(
            is_on_curve(R, TOY),
            f"G + 2G = {R} が曲線上にありません。y_R = lam * (x_P - x_R) - y_P の"
            "符号や mod の取り忘れを確認してください",
        )
        self.assertEqual(R, (851, 516))  # 3G
        self.assertEqual(
            solution.ec_add(G2, TOY.G, TOY),
            R,
            "点の足し算は可換のはずです",
        )

    def test_scalar_mul_vectors(self) -> None:
        vectors = {
            0: INFINITY,
            1: (1, 298),
            2: (818, 800),
            3: (851, 516),
            5: (550, 899),
            7: (463, 428),
            20: (421, 339),
            123: (376, 128),
            966: (1, 711),   # (n-1)G = -G
            967: INFINITY,   # nG = 単位元
        }
        for k, expected in vectors.items():
            with self.subTest(k=k):
                self.assertEqual(solution.ec_scalar_mul(k, TOY.G, TOY), expected)

    def test_scalar_mul_is_homomorphic(self) -> None:
        """(k1 + k2)G == k1*G + k2*G が成り立つことを確認します。"""
        for k1, k2 in [(3, 5), (100, 200), (966, 1), (500, 501)]:
            with self.subTest(k1=k1, k2=k2):
                lhs = solution.ec_scalar_mul((k1 + k2) % TOY.n, TOY.G, TOY)
                rhs = solution.ec_add(
                    solution.ec_scalar_mul(k1, TOY.G, TOY),
                    solution.ec_scalar_mul(k2, TOY.G, TOY),
                    TOY,
                )
                self.assertEqual(lhs, rhs)


class Part2BSecp256k1(unittest.TestCase):
    """Part 2 後半: 本物の曲線 secp256k1 でのテストです。

    スカラーは最大 256 ビットあります。ec_add を k 回繰り返す素朴な実装だと
    いつまでも終わらないので、このクラスのテストが返ってこないときは、
    まず ec_scalar_mul の実装方法を疑ってください。
    """

    def test_small_multiples(self) -> None:
        self.assertEqual(
            solution.ec_scalar_mul(2, SECP256K1.G, SECP256K1),
            (
                0xC6047F9441ED7D6D3045406E95C07CD85C778E4B8CEF3CA7ABAC09B95C709EE5,
                0x1AE168FEA63DC339A3C58419466CEAEEF7F632653266D0E1236431A950CFE52A,
            ),
        )
        self.assertEqual(
            solution.ec_scalar_mul(3, SECP256K1.G, SECP256K1),
            (
                0xF9308A019258C31049344F85F89D5229B531C845836F99B08601F113BCE036F9,
                0x388F7B0F632DE8140FE337E62A37F3566500A99934C2231B6CB9FD7584B8E672,
            ),
        )

    def test_large_scalar(self) -> None:
        self.assertEqual(
            solution.ec_scalar_mul(0xDEADBEEF12345678, SECP256K1.G, SECP256K1),
            (
                0x271AE94C558E2EFF88BB239384E52965F297CBF7065F03079BEF8DA4F79BBBEB,
                0x60FF85596544423EC7F94D2EF5E38EB33BF7A74C2A1943A6E27EB7B02C04FCBA,
            ),
        )

    def test_order_times_generator_is_identity(self) -> None:
        self.assertEqual(
            solution.ec_scalar_mul(SECP256K1.n, SECP256K1.G, SECP256K1),
            INFINITY,
            "位数 n について、nG は無限遠点になるはずです",
        )


# ---------------------------------------------------------------- Part 3
class Part3ASigmaProtocol(unittest.TestCase):
    """Part 3 前半: シグマプロトコル(対話版)のテストです。TOY 曲線を使います。"""

    X = 123           # 秘密鍵
    PUB = (376, 128)  # 公開鍵 123 * G

    def test_commit(self) -> None:
        self.assertEqual(solution.sigma_commit(456, TOY), (822, 106))

    def test_response(self) -> None:
        # s = r + e*x mod n = 456 + 77*123 mod 967 = 257
        self.assertEqual(
            solution.sigma_response(self.X, 456, 77, TOY),
            257,
            "s = r + e*x の mod は curve.n(G の位数)で取ってください。"
            "curve.p(座標の素数)と取り違えていないか確認してください",
        )

    def test_honest_transcript_accepts(self) -> None:
        """正直な証明者のトランスクリプトが必ず受理されることを確認します(完全性)。"""
        for r, e in [(456, 77), (1, 0), (966, 966), (500, 123)]:
            with self.subTest(r=r, e=e):
                R = solution.sigma_commit(r, TOY)
                s = solution.sigma_response(self.X, r, e, TOY)
                self.assertTrue(solution.sigma_verify(self.PUB, R, e, s, TOY))

    def test_wrong_response_rejects(self) -> None:
        R = solution.sigma_commit(456, TOY)
        s = solution.sigma_response(self.X, 456, 77, TOY)
        self.assertFalse(solution.sigma_verify(self.PUB, R, 77, (s + 1) % TOY.n, TOY))

    def test_wrong_pubkey_rejects(self) -> None:
        R = solution.sigma_commit(456, TOY)
        s = solution.sigma_response(self.X, 456, 77, TOY)
        other_pub = solution.ec_scalar_mul(124, TOY.G, TOY)
        self.assertFalse(solution.sigma_verify(other_pub, R, 77, s, TOY))

    def test_nonce_reuse_leaks_secret(self) -> None:
        """同じ r を 2 つのチャレンジに使うと、秘密鍵が復元できてしまうことを確認します
        (special soundness)。nonce の使い回しが致命的な理由です。"""
        r = 456
        e1, e2 = 77, 90
        s1 = solution.sigma_response(self.X, r, e1, TOY)
        s2 = solution.sigma_response(self.X, r, e2, TOY)
        # s1 - s2 = (e1 - e2) * x (mod n) から x を解きます
        n = TOY.n
        recovered = (s1 - s2) * solution.field_inv(e1 - e2, n) % n
        self.assertEqual(recovered, self.X)


class Part3BSchnorrSignature(unittest.TestCase):
    """Part 3 後半: Fiat-Shamir 変換と Schnorr 署名のテストです。secp256k1 を使います。"""

    X = 0x1B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B0B
    PUB = (
        0x53A9DEEA1228326890914787EF66CC1B3F97B360DE0CE0B8DF88AFA1A32C3343,
        0xF32366F6BBA9A724D065D5D7A6FB5B3A7DB210331B3668A9F075C19D7F94EEDB,
    )
    NONCE = 0x7E57AB1E7E57AB1E7E57AB1E7E57AB1E7E57AB1E7E57AB1E7E57AB1E7E57AB1E
    MSG = b"advanced cryptography 2026: week3"

    def test_sign_vector(self) -> None:
        """固定の鍵・nonce・メッセージに対する署名が期待値と一致することを確認します。"""
        R, s = solution.schnorr_sign(self.X, self.MSG, self.NONCE, SECP256K1)
        self.assertEqual(
            R,
            (
                0xB44CF0C87F8F960C3F5CCC6372152B4CE63F23120268A5F923747E323DD9D957,
                0x697F82FA4516C70B82F753DC2AB0DD8D8B48C5AD034DD2F191FBC77880410C13,
            ),
            "R は nonce * G になるはずです",
        )
        self.assertEqual(
            s,
            0x14DB7A64BF535569487FA73959EDFAA1B2B5E47166EB088FA5E4A48909FF9E0D,
            "s = nonce + e*x mod n のはずです。e は challenge_hash(R, pubkey,"
            " message, curve.n) で計算します。引数の順番(R が先、pubkey が"
            "後)も確認してください",
        )

    def test_roundtrip(self) -> None:
        sig = solution.schnorr_sign(self.X, self.MSG, self.NONCE, SECP256K1)
        self.assertTrue(solution.schnorr_verify(self.PUB, self.MSG, sig, SECP256K1))

    def test_tampered_message_rejects(self) -> None:
        sig = solution.schnorr_sign(self.X, self.MSG, self.NONCE, SECP256K1)
        self.assertFalse(
            solution.schnorr_verify(self.PUB, self.MSG + b"!", sig, SECP256K1),
            "別のメッセージで署名が通ってはいけません",
        )

    def test_tampered_signature_rejects(self) -> None:
        R, s = solution.schnorr_sign(self.X, self.MSG, self.NONCE, SECP256K1)
        self.assertFalse(
            solution.schnorr_verify(
                self.PUB, self.MSG, (R, (s + 1) % SECP256K1.n), SECP256K1
            )
        )

    def test_wrong_pubkey_rejects(self) -> None:
        sig = solution.schnorr_sign(self.X, self.MSG, self.NONCE, SECP256K1)
        other_pub = solution.ec_scalar_mul(self.X + 1, SECP256K1.G, SECP256K1)
        self.assertFalse(
            solution.schnorr_verify(other_pub, self.MSG, sig, SECP256K1)
        )

    def test_verify_recomputes_challenge(self) -> None:
        """検証側が e を challenge_hash で計算し直していることを確認します。

        e はメッセージに依存するので、R を固定したまま別メッセージ用の s を
        流用した署名は落ちるはずです。"""
        R, s = solution.schnorr_sign(self.X, self.MSG, self.NONCE, SECP256K1)
        e_other = challenge_hash(R, self.PUB, b"other message", SECP256K1.n)
        s_other = (self.NONCE + e_other * self.X) % SECP256K1.n
        self.assertFalse(
            solution.schnorr_verify(self.PUB, self.MSG, (R, s_other), SECP256K1)
        )


if __name__ == "__main__":
    unittest.main()
