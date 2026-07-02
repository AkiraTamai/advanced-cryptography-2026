from __future__ import annotations

import unittest

import solution


def dot(a: list[int], b: list[int], modulus: int) -> int:
    return sum(x * y for x, y in zip(a, b)) % modulus


class LweToggleTests(unittest.TestCase):
    def test_encrypt_zero_no_noise(self) -> None:
        sk = [3, 1, 4, 1]
        a = [5, 9, 2, 6]
        modulus = 97
        b = solution.lwe_encrypt(0, sk, a, 0, modulus)
        self.assertEqual(b, dot(a, sk, modulus))

    def test_encrypt_one_no_noise(self) -> None:
        sk = [3, 1, 4, 1]
        a = [5, 9, 2, 6]
        modulus = 97
        b = solution.lwe_encrypt(1, sk, a, 0, modulus)
        self.assertEqual(b, (dot(a, sk, modulus) + modulus // 2) % modulus)

    def test_encrypt_with_noise(self) -> None:
        sk = [3, 1, 4, 1]
        a = [5, 9, 2, 6]
        modulus = 97
        b = solution.lwe_encrypt(1, sk, a, 3, modulus)
        self.assertEqual(b, (dot(a, sk, modulus) + 3 + modulus // 2) % modulus)

    def test_decrypt_round_trip_zero(self) -> None:
        sk = [3, 1, 4, 1]
        a = [5, 9, 2, 6]
        modulus = 97
        for e in (-4, -1, 0, 1, 4):
            with self.subTest(e=e):
                b = solution.lwe_encrypt(0, sk, a, e, modulus)
                self.assertEqual(solution.lwe_decrypt(a, b, sk, modulus), 0)

    def test_decrypt_round_trip_one(self) -> None:
        sk = [3, 1, 4, 1]
        a = [5, 9, 2, 6]
        modulus = 97
        for e in (-4, -1, 0, 1, 4):
            with self.subTest(e=e):
                b = solution.lwe_encrypt(1, sk, a, e, modulus)
                self.assertEqual(solution.lwe_decrypt(a, b, sk, modulus), 1)

    def test_decrypt_many_keys(self) -> None:
        modulus = 97
        cases = [
            ([1, 2, 3], [10, 20, 30], 0, 2),
            ([1, 2, 3], [10, 20, 30], 1, -2),
            ([0, 0, 0, 0], [1, 1, 1, 1], 0, 0),
            ([0, 0, 0, 0], [1, 1, 1, 1], 1, 0),
        ]
        for sk, a, bit, e in cases:
            with self.subTest(sk=sk, a=a, bit=bit, e=e):
                b = solution.lwe_encrypt(bit, sk, a, e, modulus)
                self.assertEqual(solution.lwe_decrypt(a, b, sk, modulus), bit)

    def test_add_ciphertexts_is_homomorphic_xor(self) -> None:
        modulus = 97
        sk = [3, 1, 4, 1]
        cases = [
            (0, 0, 0),
            (0, 1, 1),
            (1, 0, 1),
            (1, 1, 0),
        ]
        for bit1, bit2, expected in cases:
            with self.subTest(bit1=bit1, bit2=bit2):
                a1 = [5, 9, 2, 6]
                a2 = [1, 7, 8, 3]
                b1 = solution.lwe_encrypt(bit1, sk, a1, 1, modulus)
                b2 = solution.lwe_encrypt(bit2, sk, a2, -1, modulus)
                a_sum, b_sum = solution.lwe_add((a1, b1), (a2, b2), modulus)
                self.assertEqual(a_sum, [(x + y) % modulus for x, y in zip(a1, a2)])
                self.assertEqual(b_sum, (b1 + b2) % modulus)
                self.assertEqual(
                    solution.lwe_decrypt(a_sum, b_sum, sk, modulus), expected
                )

    def test_add_ciphertexts_shape(self) -> None:
        modulus = 11
        a1, b1 = [1, 2], 3
        a2, b2 = [4, 5], 6
        a_sum, b_sum = solution.lwe_add((a1, b1), (a2, b2), modulus)
        self.assertEqual(a_sum, [5, 7])
        self.assertEqual(b_sum, 9)


if __name__ == "__main__":
    unittest.main()
