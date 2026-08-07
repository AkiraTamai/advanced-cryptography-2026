"""Week 2 `toy-mpc`の公開採点テストです。

リポジトリ直下で次を実行してください。

    bash scripts/test-python-submission.sh week2 toy-mpc <github-username>
"""

from __future__ import annotations

import itertools
import unittest
from unittest import mock

import solution
from given import OT_P, OT_Q, derive_pad, xor_bytes


MODULUS = 67


def make_shared(value: int, seed: int, parties: int = 3) -> list[int]:
    randomness = [seed + 3 * i for i in range(parties - 1)]
    return solution.share(value, randomness, MODULUS)


def make_triple(a: int, b: int, seed: int, parties: int = 3):
    return (
        make_shared(a, seed, parties),
        make_shared(b, seed + 7, parties),
        make_shared(a * b, seed + 14, parties),
    )


class PartA1Sharing(unittest.TestCase):
    def test_fixed_vector(self) -> None:
        self.assertEqual(solution.share(42, [5, 11], MODULUS), [5, 11, 26])
        self.assertEqual(solution.share(-3, [70, -2], MODULUS), [3, 65, 63])

    def test_share_and_reconstruct(self) -> None:
        for secret, randomness in [
            (0, [0]),
            (42, [5, 11]),
            (-20, [100, -50]),
            (10**30, [123, 456, 789]),
        ]:
            with self.subTest(secret=secret, parties=len(randomness) + 1):
                shares = solution.share(secret, randomness, MODULUS)
                self.assertEqual(len(shares), len(randomness) + 1)
                self.assertTrue(all(0 <= value < MODULUS for value in shares))
                self.assertEqual(
                    solution.reconstruct(shares, MODULUS),
                    secret % MODULUS,
                )

    def test_same_secret_can_have_different_shares(self) -> None:
        first = solution.share(42, [5, 11], MODULUS)
        second = solution.share(42, [20, 30], MODULUS)
        self.assertNotEqual(first, second)
        self.assertEqual(solution.reconstruct(first, MODULUS), 42)
        self.assertEqual(solution.reconstruct(second, MODULUS), 42)

    def test_invalid_inputs_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solution.share(1, [], MODULUS)
        with self.assertRaises(ValueError):
            solution.reconstruct([1], MODULUS)
        for modulus in (1, 0, -7):
            with self.subTest(modulus=modulus):
                with self.assertRaises(ValueError):
                    solution.share(1, [2], modulus)
                with self.assertRaises(ValueError):
                    solution.reconstruct([1, 2], modulus)


class PartA2LocalAddition(unittest.TestCase):
    def test_fixed_vector(self) -> None:
        left = [3, 20, 56]   # shares of 12
        right = [4, 30, 28]  # shares of -5 == 62
        self.assertEqual(
            solution.add_shares(left, right, MODULUS),
            [7, 50, 17],
        )

    def test_addition_reconstructs_to_sum(self) -> None:
        for parties, left_value, right_value in [
            (2, 12, 9),
            (3, -5, 11),
            (4, 66, 10**20),
        ]:
            with self.subTest(parties=parties):
                left = make_shared(left_value, 2, parties)
                right = make_shared(right_value, 17, parties)
                output = solution.add_shares(left, right, MODULUS)
                self.assertEqual(len(output), parties)
                self.assertEqual(
                    solution.reconstruct(output, MODULUS),
                    (left_value + right_value) % MODULUS,
                )

    def test_addition_does_not_open(self) -> None:
        with mock.patch.object(
            solution,
            "reconstruct",
            side_effect=AssertionError("add_shares must not open its inputs"),
        ):
            self.assertEqual(
                solution.add_shares([1, 2], [3, 4], MODULUS),
                [4, 6],
            )

    def test_mismatched_party_counts_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solution.add_shares([1, 2], [3, 4, 5], MODULUS)


class PartA3BeaverMultiplication(unittest.TestCase):
    def test_fixed_share_vector(self) -> None:
        x_shares = [3, 20, 56]  # shares of 12
        y_shares = [4, 30, 28]  # shares of -5 == 62
        triple = (
            [1, 2, 4],       # shares of a = 7
            [6, 1, 2],       # shares of b = 9
            [10, 20, 33],    # shares of c = 63 == 7*9
        )
        self.assertEqual(
            solution.beaver_multiply(
                x_shares,
                y_shares,
                triple,
                MODULUS,
            ),
            [23, 64, 54],
        )

    def test_products_for_two_and_three_parties(self) -> None:
        for parties, x, y, a, b in [
            (2, 12, 9, 4, 7),
            (3, -5, 11, 8, 3),
            (3, 0, 66, 10, 20),
        ]:
            with self.subTest(parties=parties, x=x, y=y):
                output = solution.beaver_multiply(
                    make_shared(x, 2, parties),
                    make_shared(y, 5, parties),
                    make_triple(a, b, 8, parties),
                    MODULUS,
                )
                self.assertEqual(len(output), parties)
                self.assertEqual(
                    solution.reconstruct(output, MODULUS),
                    (x * y) % MODULUS,
                )

    def test_opens_exactly_the_two_masked_differences(self) -> None:
        x_shares = make_shared(12, 2)
        y_shares = make_shared(9, 5)
        triple = make_triple(4, 7, 8)
        expected_d = solution.sub_shares(x_shares, triple[0], MODULUS)
        expected_e = solution.sub_shares(y_shares, triple[1], MODULUS)

        with mock.patch.object(
            solution,
            "reconstruct",
            wraps=solution.reconstruct,
        ) as opening:
            solution.beaver_multiply(
                x_shares,
                y_shares,
                triple,
                MODULUS,
            )

        self.assertEqual(opening.call_count, 2)
        opened_vectors = [call.args[0] for call in opening.call_args_list]
        self.assertEqual(opened_vectors, [expected_d, expected_e])

    def test_mismatched_party_counts_rejected(self) -> None:
        triple = ([1, 2, 3], [4, 5, 6], [7, 8, 9])
        with self.assertRaises(ValueError):
            solution.beaver_multiply([1, 2], [3, 4, 5], triple, MODULUS)
        with self.assertRaises(ValueError):
            solution.beaver_multiply(
                [1, 2, 3],
                [4, 5, 6],
                ([1, 2], [3, 4, 5], [6, 7, 8]),
                MODULUS,
            )


class PartB1ObliviousTransfer(unittest.TestCase):
    def test_setup_and_request_vectors(self) -> None:
        # A = 2^3 = 8 mod 23; g^4 = 16.
        sender_public = solution.ot_sender_setup(3)
        self.assertEqual(sender_public, 8)
        self.assertEqual(solution.ot_receiver_request(sender_public, 0, 0), 1)
        self.assertEqual(solution.ot_receiver_request(sender_public, 1, 0), 8)
        self.assertEqual(solution.ot_receiver_request(sender_public, 0, 4), 16)
        self.assertEqual(
            solution.ot_receiver_request(sender_public, 1, 4),
            13,  # 8 * 16 mod 23
        )

    def test_both_choices_round_trip(self) -> None:
        messages = (b"left!", b"right")
        for choice, sender_secret, receiver_secret in [
            (0, 3, 0),
            (1, 3, 0),
            (0, 3, 4),
            (1, 3, 4),
            (0, 7, 2),
            (1, 9, 10),
        ]:
            with self.subTest(choice=choice, a=sender_secret, b=receiver_secret):
                sender_public = solution.ot_sender_setup(sender_secret)
                request = solution.ot_receiver_request(
                    sender_public,
                    choice,
                    receiver_secret,
                )
                ciphertexts = solution.ot_sender_encrypt(
                    sender_secret,
                    request,
                    messages[0],
                    messages[1],
                )
                recovered = solution.ot_receiver_decrypt(
                    sender_public,
                    choice,
                    receiver_secret,
                    ciphertexts,
                )
                self.assertEqual(recovered, messages[choice])

    def test_chosen_key_does_not_directly_decrypt_other_branch(self) -> None:
        sender_secret = 3
        receiver_secret = 4
        messages = (b"alpha", b"bravo")
        sender_public = solution.ot_sender_setup(sender_secret)
        request = solution.ot_receiver_request(sender_public, 0, receiver_secret)
        ciphertexts = solution.ot_sender_encrypt(
            sender_secret,
            request,
            messages[0],
            messages[1],
        )

        chosen_shared = pow(sender_public, receiver_secret, OT_P)
        wrong_plaintext = xor_bytes(
            ciphertexts[1],
            derive_pad(chosen_shared, 1, len(ciphertexts[1])),
        )
        self.assertNotEqual(wrong_plaintext, messages[1])

    def test_invalid_inputs_rejected(self) -> None:
        sender_public = solution.ot_sender_setup(3)
        for choice in (-1, 2):
            with self.subTest(choice=choice):
                with self.assertRaises(ValueError):
                    solution.ot_receiver_request(sender_public, choice, 4)
                with self.assertRaises(ValueError):
                    solution.ot_receiver_decrypt(
                        sender_public,
                        choice,
                        4,
                        (b"x", b"y"),
                    )
        for receiver_secret in (-1, OT_Q):
            with self.subTest(receiver_secret=receiver_secret):
                with self.assertRaises(ValueError):
                    solution.ot_receiver_request(
                        sender_public,
                        0,
                        receiver_secret,
                    )
                with self.assertRaises(ValueError):
                    solution.ot_receiver_decrypt(
                        sender_public,
                        0,
                        receiver_secret,
                        (b"x", b"y"),
                    )
        for sender_secret in (0, OT_Q):
            with self.subTest(sender_secret=sender_secret):
                with self.assertRaises(ValueError):
                    solution.ot_sender_setup(sender_secret)
                with self.assertRaises(ValueError):
                    solution.ot_sender_encrypt(
                        sender_secret,
                        1,
                        b"a",
                        b"b",
                    )
        with self.assertRaises(ValueError):
            solution.ot_sender_encrypt(3, 5, b"short", b"longer")
        with self.assertRaises(ValueError):
            solution.ot_sender_encrypt(3, 0, b"a", b"b")


class PartB2GMW(unittest.TestCase):
    def test_provided_xor_helpers(self) -> None:
        first = solution.xor_share(1, 0)
        second = solution.xor_share(0, 1)
        self.assertEqual(solution.xor_reconstruct(first), 1)
        self.assertEqual(solution.xor_reconstruct(second), 0)
        self.assertEqual(
            solution.xor_reconstruct(solution.xor_shares(first, second)),
            1,
        )

    def test_gmw_and_all_share_patterns(self) -> None:
        bit_shares = list(itertools.product((0, 1), repeat=2))
        for index, (x_shares, y_shares) in enumerate(
            itertools.product(bit_shares, repeat=2)
        ):
            masks = (index & 1, (index >> 1) & 1)
            output = solution.gmw_and(
                x_shares,
                y_shares,
                masks,
                ((3, 4), (5, 6)),
            )
            with self.subTest(x_shares=x_shares, y_shares=y_shares):
                self.assertIn(output[0], (0, 1))
                self.assertIn(output[1], (0, 1))
                self.assertEqual(
                    solution.xor_reconstruct(output),
                    solution.xor_reconstruct(x_shares)
                    & solution.xor_reconstruct(y_shares),
                )

    def test_fixed_output_shares(self) -> None:
        self.assertEqual(
            solution.gmw_and(
                (1, 0),
                (0, 1),
                (1, 0),
                ((3, 4), (5, 6)),
            ),
            (1, 0),
        )

    def test_gmw_and_runs_two_ot_sessions(self) -> None:
        with mock.patch.object(
            solution,
            "_ot_transfer_bit",
            wraps=solution._ot_transfer_bit,
        ) as transfer:
            output = solution.gmw_and(
                (1, 1),
                (1, 0),
                (0, 1),
                ((3, 4), (5, 6)),
            )
        self.assertEqual(transfer.call_count, 2)
        self.assertEqual(solution.xor_reconstruct(output), 0)

    def test_invalid_bits_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solution.gmw_and(
                (0, 1),
                (1, 0),
                (0, 3),
                ((3, 4), (5, 6)),
            )
        with self.assertRaises(ValueError):
            solution.gmw_and(
                (0, 1),
                (1, 0),
                (0, 1),
                ((3, 4),),
            )


if __name__ == "__main__":
    unittest.main()
