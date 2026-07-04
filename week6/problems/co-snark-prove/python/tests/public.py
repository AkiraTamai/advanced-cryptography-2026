from __future__ import annotations

import unittest

import solution


def make_wire_shares(
    witness: list[int],
    randomness_per_wire: list[list[int]],
    modulus: int,
) -> list[list[int]]:
    """Secret-share each witness wire independently."""
    return [
        solution.share(w, r, modulus)
        for w, r in zip(witness, randomness_per_wire)
    ]


class CoSnarkProveTests(unittest.TestCase):
    def test_linear_combination_matches_plaintext(self) -> None:
        modulus = 97
        witness = [3, 5]
        coeffs = [1, 2]
        wire_shares = make_wire_shares(witness, [[1], [2]], modulus)  # 2 parties

        result = solution.linear_combination_shares(coeffs, wire_shares, modulus)
        expected = sum(c * w for c, w in zip(coeffs, witness)) % modulus
        self.assertEqual(solution.reconstruct(result, modulus), expected)

    def test_linear_combination_three_parties(self) -> None:
        modulus = 101
        witness = [12, 7, 4]
        coeffs = [5, 3, 9]
        wire_shares = make_wire_shares(
            witness, [[1, 2], [3, 4], [5, 6]], modulus
        )  # 3 parties

        result = solution.linear_combination_shares(coeffs, wire_shares, modulus)
        self.assertEqual(len(result), 3)
        expected = sum(c * w for c, w in zip(coeffs, witness)) % modulus
        self.assertEqual(solution.reconstruct(result, modulus), expected)

    def test_linear_combination_preserves_a_single_wire(self) -> None:
        modulus = 97
        wire_shares = make_wire_shares([42], [[13]], modulus)
        result = solution.linear_combination_shares([1], wire_shares, modulus)
        self.assertEqual(solution.reconstruct(result, modulus), 42)

    def test_mpc_prove_matches_single_prover(self) -> None:
        modulus = 97
        witness = [3, 5]
        coeffs_a = [1, 2]  # A = 1*3 + 2*5 = 13
        coeffs_b = [4, 1]  # B = 4*3 + 1*5 = 17
        wire_shares = make_wire_shares(witness, [[1], [2]], modulus)

        # Beaver triple: a = 5, b = 9, c = a*b = 45.
        triple = (
            solution.share(5, [1], modulus),
            solution.share(9, [4], modulus),
            solution.share(45, [20], modulus),
        )

        a_sh, b_sh, c_sh = solution.mpc_prove(
            coeffs_a, coeffs_b, wire_shares, triple, modulus
        )

        expected_a = sum(c * w for c, w in zip(coeffs_a, witness)) % modulus
        expected_b = sum(c * w for c, w in zip(coeffs_b, witness)) % modulus
        expected_c = (expected_a * expected_b) % modulus

        self.assertEqual(solution.reconstruct(a_sh, modulus), expected_a)  # 13
        self.assertEqual(solution.reconstruct(b_sh, modulus), expected_b)  # 17
        self.assertEqual(solution.reconstruct(c_sh, modulus), expected_c)  # 27

    def test_mpc_prove_three_parties(self) -> None:
        modulus = 101
        witness = [2, 9, 1]
        coeffs_a = [1, 1, 1]  # A = 2 + 9 + 1 = 12
        coeffs_b = [0, 1, 3]  # B = 9 + 3 = 12
        wire_shares = make_wire_shares(
            witness, [[3, 4], [5, 6], [7, 8]], modulus
        )
        triple = (
            solution.share(4, [1, 1], modulus),
            solution.share(20, [5, 5], modulus),
            solution.share(80, [10, 10], modulus),  # c = a*b = 80
        )

        a_sh, b_sh, c_sh = solution.mpc_prove(
            coeffs_a, coeffs_b, wire_shares, triple, modulus
        )
        expected_a = sum(c * w for c, w in zip(coeffs_a, witness)) % modulus
        expected_b = sum(c * w for c, w in zip(coeffs_b, witness)) % modulus
        self.assertEqual(len(a_sh), 3)
        self.assertEqual(solution.reconstruct(a_sh, modulus), expected_a)  # 12
        self.assertEqual(solution.reconstruct(b_sh, modulus), expected_b)  # 12
        self.assertEqual(
            solution.reconstruct(c_sh, modulus), (expected_a * expected_b) % modulus
        )

    def test_mpc_prove_with_zero_linear_form(self) -> None:
        modulus = 89
        witness = [6, 6]
        coeffs_a = [1, 1]   # A = 12
        coeffs_b = [1, 88]  # B = 6 + 88*6 = 6 - 6 = 0 (mod 89)
        wire_shares = make_wire_shares(witness, [[2], [3]], modulus)
        triple = (
            solution.share(3, [2], modulus),
            solution.share(6, [1], modulus),
            solution.share(18, [9], modulus),  # c = a*b = 18
        )

        a_sh, b_sh, c_sh = solution.mpc_prove(
            coeffs_a, coeffs_b, wire_shares, triple, modulus
        )
        self.assertEqual(solution.reconstruct(b_sh, modulus), 0)
        # C = A * B = 12 * 0 = 0
        self.assertEqual(solution.reconstruct(c_sh, modulus), 0)

    def test_proof_elements_are_shared_not_plaintext(self) -> None:
        modulus = 97
        witness = [3, 5]
        wire_shares = make_wire_shares(witness, [[1], [2]], modulus)
        triple = (
            solution.share(5, [1], modulus),
            solution.share(9, [4], modulus),
            solution.share(45, [20], modulus),
        )
        a_sh, b_sh, c_sh = solution.mpc_prove(
            [1, 2], [4, 1], wire_shares, triple, modulus
        )
        # Each proof element is returned as a per-party share vector, not an int.
        for shares in (a_sh, b_sh, c_sh):
            self.assertIsInstance(shares, list)
            self.assertEqual(len(shares), 2)


if __name__ == "__main__":
    unittest.main()
