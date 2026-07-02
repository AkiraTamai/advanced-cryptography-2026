from __future__ import annotations

import unittest

import solution


class SecretShareMpcTests(unittest.TestCase):
    def test_share_reconstruct_round_trip(self) -> None:
        modulus = 97
        secret = 42
        randomness = [10, 55, 3]
        shares = solution.share(secret, randomness, modulus)
        self.assertEqual(len(shares), len(randomness) + 1)
        self.assertEqual(solution.reconstruct(shares, modulus), secret)

    def test_share_reconstruct_negative_and_large_randomness(self) -> None:
        modulus = 101
        secret = 7
        randomness = [-40, 250, -3]
        shares = solution.share(secret, randomness, modulus)
        self.assertEqual(solution.reconstruct(shares, modulus), secret % modulus)
        for s in shares:
            self.assertTrue(0 <= s < modulus)

    def test_add_shares_result_is_reduced_mod_modulus(self) -> None:
        modulus = 13
        # Each individual share is already canonical (< 13), but the
        # component-wise sums (10+8=18, 2+8=10) cross the modulus boundary,
        # so add_shares must reduce mod `modulus`, not just add the ints.
        shares_a = [10, 2]
        shares_b = [8, 8]
        summed = solution.add_shares(shares_a, shares_b, modulus)
        for s in summed:
            self.assertTrue(0 <= s < modulus)
        expected_secret = (solution.reconstruct(shares_a, modulus) + solution.reconstruct(shares_b, modulus)) % modulus
        self.assertEqual(solution.reconstruct(summed, modulus), expected_secret)

    def test_scale_shares_result_is_reduced_mod_modulus(self) -> None:
        modulus = 13
        shares = [5, 9]
        scaled = solution.scale_shares(shares, 7, modulus)
        for s in scaled:
            self.assertTrue(0 <= s < modulus)
        expected_secret = (solution.reconstruct(shares, modulus) * 7) % modulus
        self.assertEqual(solution.reconstruct(scaled, modulus), expected_secret)

    def test_add_shares_is_local_and_linear(self) -> None:
        modulus = 97
        shares_a = solution.share(20, [5, 6], modulus)
        shares_b = solution.share(30, [1, 2], modulus)
        summed = solution.add_shares(shares_a, shares_b, modulus)
        self.assertEqual(solution.reconstruct(summed, modulus), (20 + 30) % modulus)

    def test_scale_shares_is_local_and_linear(self) -> None:
        modulus = 97
        shares = solution.share(11, [4, 9], modulus)
        scaled = solution.scale_shares(shares, 6, modulus)
        self.assertEqual(solution.reconstruct(scaled, modulus), (11 * 6) % modulus)

    def test_beaver_multiply_two_parties(self) -> None:
        modulus = 97
        # x = 6, y = 7 -> expect x*y = 42
        x_shares = solution.share(6, [2], modulus)
        y_shares = solution.share(7, [3], modulus)
        # Beaver triple: a = 5, b = 9, c = a*b = 45
        a_shares = solution.share(5, [1], modulus)
        b_shares = solution.share(9, [4], modulus)
        c_shares = solution.share(45, [20], modulus)

        z_shares = solution.beaver_multiply(
            x_shares, y_shares, a_shares, b_shares, c_shares, modulus
        )
        self.assertEqual(len(z_shares), 2)
        self.assertEqual(solution.reconstruct(z_shares, modulus), (6 * 7) % modulus)

    def test_beaver_multiply_three_parties(self) -> None:
        modulus = 101
        x_shares = solution.share(12, [3, 40], modulus)
        y_shares = solution.share(15, [7, 60], modulus)
        a_shares = solution.share(4, [1, 1], modulus)
        b_shares = solution.share(20, [5, 5], modulus)
        c_shares = solution.share(80, [10, 10], modulus)  # c = a * b = 80

        z_shares = solution.beaver_multiply(
            x_shares, y_shares, a_shares, b_shares, c_shares, modulus
        )
        self.assertEqual(len(z_shares), 3)
        self.assertEqual(solution.reconstruct(z_shares, modulus), (12 * 15) % modulus)

    def test_beaver_multiply_with_zero_operand(self) -> None:
        modulus = 89
        x_shares = solution.share(0, [30], modulus)
        y_shares = solution.share(17, [8], modulus)
        a_shares = solution.share(3, [2], modulus)
        b_shares = solution.share(6, [1], modulus)
        c_shares = solution.share(18, [9], modulus)  # c = a * b = 18

        z_shares = solution.beaver_multiply(
            x_shares, y_shares, a_shares, b_shares, c_shares, modulus
        )
        self.assertEqual(solution.reconstruct(z_shares, modulus), 0)

    def test_no_single_share_reveals_the_secret(self) -> None:
        modulus = 97
        shares_low = solution.share(3, [50], modulus)
        shares_high = solution.share(90, [50], modulus)
        # Both secrets share the exact same first share; the secret is not
        # determined by any individual share on its own.
        self.assertEqual(shares_low[0], shares_high[0])
        self.assertNotEqual(
            solution.reconstruct(shares_low, modulus),
            solution.reconstruct(shares_high, modulus),
        )


if __name__ == "__main__":
    unittest.main()
