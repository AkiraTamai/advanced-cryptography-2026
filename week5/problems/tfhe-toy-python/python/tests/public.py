from __future__ import annotations

import random
import unittest

import solution


class ToyTFHETests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = solution.ToyTFHEParams()
        self.rng = random.Random(2026)
        self.lwe_key = solution.generate_lwe_secret_key(self.params, self.rng)
        self.rlwe_key = solution.generate_rlwe_secret_key(self.params, self.rng)
        self.evaluation_key = solution.make_evaluation_key(
            self.lwe_key,
            self.rlwe_key,
            self.params,
            self.rng,
        )

    def test_default_parameters_are_fixed(self) -> None:
        self.assertEqual(self.params.k, 4)
        self.assertEqual(self.params.p, 8)
        self.assertEqual(self.params.n, 16)
        self.assertEqual(self.params.q, 32)
        self.assertEqual(self.params.delta, 4)
        self.assertEqual(self.params.noise_bound, 1)
        self.assertEqual(self.params.evaluation_key_noise_bound, 0)
        self.assertEqual(self.params.B, 2)
        self.assertEqual(self.params.l, 5)
        self.assertEqual(self.params.hom_nand_constant, 1)

    def test_polynomial_multiplication_is_negacyclic(self) -> None:
        x_to_n_minus_1 = solution.monomial_poly(self.params.n - 1, self.params)
        x = solution.monomial_poly(1, self.params)
        product = solution.poly_mul(x_to_n_minus_1, x, self.params)
        expected = [self.params.q - 1] + [0 for _ in range(self.params.n - 1)]
        self.assertEqual(product, expected)

    def test_plaintext_is_scaled_from_zp_to_zq(self) -> None:
        self.assertEqual(solution.scale_plaintext(1, self.params), 4)
        self.assertEqual(solution.scale_plaintext(7, self.params), 28)

    def test_ciphertext_coefficients_are_rescaled_to_rotation_indices(self) -> None:
        self.assertEqual(self.params.q, 2 * self.params.n)
        self.assertEqual(solution.rescale_q_to_2n(0, self.params), 0)
        self.assertEqual(
            solution.rescale_q_to_2n(
                solution.scale_plaintext(1, self.params),
                self.params,
            ),
            4,
        )
        self.assertEqual(
            solution.rescale_q_to_2n(
                solution.scale_plaintext(7, self.params),
                self.params,
            ),
            28,
        )

    def test_lwe_encrypt_decrypt_round_trip(self) -> None:
        for message in solution.bit_plaintext_candidates(self.params):
            with self.subTest(message=message):
                scaled_message = self.params.delta * message
                ciphertext = solution.encrypt_lwe(
                    scaled_message,
                    self.lwe_key,
                    self.params,
                    self.rng,
                )
                self.assertEqual(
                    solution.decrypt_lwe(
                        ciphertext,
                        self.lwe_key,
                        self.params,
                    ),
                    message,
                )

    def test_lwe_add_adds_encrypted_plaintexts(self) -> None:
        left_message = 2
        right_message = 3
        left = solution.encrypt_lwe(
            self.params.delta * left_message,
            self.lwe_key,
            self.params,
            self.rng,
        )
        right = solution.encrypt_lwe(
            self.params.delta * right_message,
            self.lwe_key,
            self.params,
            self.rng,
        )
        added = solution.lwe_add(left, right, self.params)

        self.assertEqual(
            solution.decrypt_lwe(added, self.lwe_key, self.params),
            solution.normalize(left_message + right_message, self.params.p),
        )

    def test_lwe_scalar_mul_multiplies_encrypted_plaintext(self) -> None:
        message = 2
        scalar = 3
        ciphertext = solution.trivial_lwe(
            self.params.delta * message,
            self.params,
        )
        multiplied = solution.lwe_scalar_mul(ciphertext, scalar, self.params)

        self.assertEqual(
            solution.decrypt_lwe(multiplied, self.lwe_key, self.params),
            solution.normalize(scalar * message, self.params.p),
        )

    def test_gadget_decomposition_matches_slide_formula(self) -> None:
        self.assertEqual(solution.gadget_weights(self.params), [16, 8, 4, 2, 1])
        self.assertEqual(
            solution.gadget_decompose(29, self.params),
            [1, 1, 1, 0, 1],
        )

        decomposed = solution.gadget_decompose_poly(
            [29, 2, 0, 31] + [0 for _ in range(self.params.n - 4)],
            self.params,
        )
        self.assertEqual(
            decomposed[0],
            [1, 0, 0, 1] + [0 for _ in range(self.params.n - 4)],
        )
        self.assertEqual(
            decomposed[1],
            [1, 0, 0, 1] + [0 for _ in range(self.params.n - 4)],
        )
        self.assertEqual(
            decomposed[2],
            [1, 0, 0, 1] + [0 for _ in range(self.params.n - 4)],
        )
        self.assertEqual(
            decomposed[3],
            [0, 1, 0, 1] + [0 for _ in range(self.params.n - 4)],
        )
        self.assertEqual(
            decomposed[4],
            [1, 0, 0, 1] + [0 for _ in range(self.params.n - 4)],
        )

    def test_rlwe_encrypt_decrypt_round_trip(self) -> None:
        message = [3, 1, 4, 1, 5] + [0 for _ in range(self.params.n - 5)]
        ciphertext = solution.encrypt_rlwe(
            solution.scale_plaintext_poly(message, self.params),
            self.rlwe_key,
            self.params,
            self.rng,
        )
        self.assertEqual(
            solution.decrypt_rlwe(
                ciphertext,
                self.rlwe_key,
                self.params,
            ),
            message,
        )

    def test_cmux_selects_false_branch_when_control_is_zero(self) -> None:
        control = solution.rgsw_encrypt_bit(
            0,
            self.rlwe_key,
            self.params,
            self.rng,
        )
        false_message = solution.constant_poly(3, self.params)
        true_message = solution.constant_poly(6, self.params)
        selected = solution.cmux(
            control,
            solution.trivial_rlwe_plaintext(false_message, self.params),
            solution.trivial_rlwe_plaintext(true_message, self.params),
            self.params,
        )
        self.assertEqual(
            solution.decrypt_rlwe(
                selected,
                self.rlwe_key,
                self.params,
            ),
            false_message,
        )

    def test_external_product_multiplies_by_encrypted_control_bit(self) -> None:
        message = [3, 1, 4, 1] + [0 for _ in range(self.params.n - 4)]
        ciphertext = solution.encrypt_rlwe(
            solution.scale_plaintext_poly(message, self.params),
            self.rlwe_key,
            self.params,
            self.rng,
        )

        control_zero = solution.rgsw_encrypt_bit(
            0,
            self.rlwe_key,
            self.params,
            self.rng,
        )
        product_zero = solution.external_product(
            control_zero,
            ciphertext,
            self.params,
        )
        self.assertEqual(
            solution.decrypt_rlwe(
                product_zero,
                self.rlwe_key,
                self.params,
            ),
            solution.zero_poly(self.params),
        )

        control_one = solution.rgsw_encrypt_bit(
            1,
            self.rlwe_key,
            self.params,
            self.rng,
        )
        product_one = solution.external_product(
            control_one,
            ciphertext,
            self.params,
        )
        self.assertEqual(
            solution.decrypt_rlwe(
                product_one,
                self.rlwe_key,
                self.params,
            ),
            message,
        )

    def test_cmux_selects_true_branch_when_control_is_one(self) -> None:
        control = solution.rgsw_encrypt_bit(
            1,
            self.rlwe_key,
            self.params,
            self.rng,
        )
        false_message = solution.constant_poly(3, self.params)
        true_message = solution.constant_poly(6, self.params)
        selected = solution.cmux(
            control,
            solution.trivial_rlwe_plaintext(false_message, self.params),
            solution.trivial_rlwe_plaintext(true_message, self.params),
            self.params,
        )
        self.assertEqual(
            solution.decrypt_rlwe(
                selected,
                self.rlwe_key,
                self.params,
            ),
            true_message,
        )

    def test_blind_rotation_places_test_polynomial_coefficient_at_constant_term(self) -> None:
        ciphertext = solution.trivial_lwe_plaintext(3, self.params)
        test_polynomial = [
            index % self.params.p
            for index in range(self.params.n)
        ]
        rotated = solution.blind_rotate(
            ciphertext,
            test_polynomial,
            self.evaluation_key.bootstrapping_key,
            self.params,
        )
        decrypted = solution.decrypt_rlwe(
            rotated,
            self.rlwe_key,
            self.params,
        )
        rescaled = solution.rescale_lwe_ciphertext(ciphertext, self.params)
        self.assertEqual(ciphertext.b, 12)
        self.assertEqual(rescaled.b, 12)
        self.assertEqual(decrypted[0], test_polynomial[rescaled.b])

    def test_sample_extract_preserves_constant_term_under_extracted_key(self) -> None:
        message = [7, 6, 5, 4] + [0 for _ in range(self.params.n - 4)]
        rlwe_ciphertext = solution.encrypt_rlwe(
            solution.scale_plaintext_poly(message, self.params),
            self.rlwe_key,
            self.params,
            self.rng,
        )
        extracted = solution.sample_extract(rlwe_ciphertext, self.params)
        extracted_key = solution.extracted_lwe_key_from_rlwe_key(
            self.rlwe_key,
            self.params,
        )
        expected_a = [rlwe_ciphertext.a[0]]
        for index in range(1, self.params.n):
            coefficient = -rlwe_ciphertext.a[self.params.n - index]
            expected_a.append(solution.normalize(coefficient, self.params.q))

        self.assertEqual(extracted.a, expected_a)
        self.assertEqual(extracted_key, self.rlwe_key)
        self.assertEqual(
            solution.decrypt_lwe(extracted, extracted_key, self.params),
            message[0],
        )

    def test_key_switch_preserves_plaintext_under_original_lwe_key(self) -> None:
        message = [7, 6, 5, 4] + [0 for _ in range(self.params.n - 4)]
        rlwe_ciphertext = solution.encrypt_rlwe(
            solution.scale_plaintext_poly(message, self.params),
            self.rlwe_key,
            self.params,
            self.rng,
        )
        extracted = solution.sample_extract(rlwe_ciphertext, self.params)
        switched = solution.key_switch(
            extracted,
            self.evaluation_key.key_switching_key,
            self.params,
        )
        self.assertEqual(
            solution.decrypt_lwe(switched, self.lwe_key, self.params),
            message[0],
        )

    def test_programmable_bootstrap_matches_each_step(self) -> None:
        ciphertext = solution.trivial_lwe_plaintext(3, self.params)
        test_polynomial: list[int] = []
        for coefficient in self.params.nand_test_polynomial:
            test_polynomial.append(coefficient)

        rotated = solution.blind_rotate(
            ciphertext,
            test_polynomial,
            self.evaluation_key.bootstrapping_key,
            self.params,
        )
        extracted = solution.sample_extract(rotated, self.params)
        expected = solution.key_switch(
            extracted,
            self.evaluation_key.key_switching_key,
            self.params,
        )
        bootstrapped = solution.programmable_bootstrap(
            ciphertext,
            self.evaluation_key,
            self.params,
        )

        self.assertEqual(bootstrapped, expected)

    def test_hom_nand_truth_table(self) -> None:
        cases = [
            (0, 0, 1),
            (1, 0, 1),
            (0, 1, 1),
            (1, 1, 0),
        ]
        for left_bit, right_bit, expected_bit in cases:
            with self.subTest(left_bit=left_bit, right_bit=right_bit):
                left_message = (
                    self.params.delta
                    * solution.encode_bit(left_bit, self.params)
                )
                left = solution.encrypt_lwe(
                    left_message,
                    self.lwe_key,
                    self.params,
                    self.rng,
                )
                right_message = (
                    self.params.delta
                    * solution.encode_bit(right_bit, self.params)
                )
                right = solution.encrypt_lwe(
                    right_message,
                    self.lwe_key,
                    self.params,
                    self.rng,
                )
                result = solution.hom_nand(
                    left,
                    right,
                    self.evaluation_key,
                    self.params,
                )
                message = solution.decrypt_lwe(
                    result,
                    self.lwe_key,
                    self.params,
                )
                self.assertEqual(solution.decode_bit(message, self.params), expected_bit)

    def test_hom_nand_test_polynomial_has_only_one_coefficients(self) -> None:
        self.assertEqual(
            self.params.nand_test_polynomial,
            tuple(1 for _ in range(self.params.n)),
        )

    def test_hom_nand_handles_all_input_noise_values(self) -> None:
        for left_bit in (0, 1):
            for right_bit in (0, 1):
                for left_error in (0, 1):
                    for right_error in (0, 1):
                        with self.subTest(
                            left_bit=left_bit,
                            right_bit=right_bit,
                            left_error=left_error,
                            right_error=right_error,
                        ):
                            left_message = (
                                self.params.delta
                                * solution.encode_bit(left_bit, self.params)
                            )
                            right_message = (
                                self.params.delta
                                * solution.encode_bit(right_bit, self.params)
                            )
                            left = solution.trivial_lwe(
                                left_message + left_error,
                                self.params,
                            )
                            right = solution.trivial_lwe(
                                right_message + right_error,
                                self.params,
                            )
                            result = solution.hom_nand(
                                left,
                                right,
                                self.evaluation_key,
                                self.params,
                            )
                            message = solution.decrypt_lwe(
                                result,
                                self.lwe_key,
                                self.params,
                            )
                            expected = 1 - (left_bit & right_bit)
                            self.assertEqual(
                                solution.decode_bit(message, self.params),
                                expected,
                            )


if __name__ == "__main__":
    unittest.main()
