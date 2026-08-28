import itertools
import random


class Polynomial:
    """Class representing a multivariate polynomial.

    terms: terms of a polynomial
    p: order of finite field (a prime number)

    e.g.)
        x*y + x + 2 = {
            (1,1): 1,
            (1,0): 1,
            (0,0): 2
        }
    """

    def __init__(
        self,
        terms: dict[tuple[int, ...], int],
        p: int
    ) -> None:
        self.terms = terms
        self.p = p

    def reduce(self, x: int) -> int:
        return x % self.p

    def evaluate(self, point: tuple[int, ...]) -> int:
        """Evaluate the multivariate polynomial at a given point."""
        if len(point) != len(next(iter(self.terms))):
            raise ValueError("Point dimension does not match polynomial.")

        result = 0

        for exponents, coefficient in self.terms.items():
            term = coefficient % self.p

            for x, exponent in zip(point, exponents):
                term *= pow(x % self.p, exponent, self.p)
                term %= self.p

            result += term
            result %= self.p

        return result


class UnivariatePolynomial(Polynomial):
    """Class representing a univariate polynomial."""

    def __init__(
        self,
        coefficients: list[int],
        p: int
    ) -> None:
        self.coefficients = coefficients
        self.p = p

    def evaluate(self, x: int) -> int:
        """Evaluate the univariate polynomial at x."""
        x %= self.p
        result = 0

        # Horner's method
        for coefficient in reversed(self.coefficients):
            result = (result * x + coefficient) % self.p

        return result


class SumCheck:
    """Class representing SumCheck protocol."""

    def __init__(
        self,
        polynomial: Polynomial
    ) -> None:
        self.f = polynomial
        self.p = polynomial.p
        self.n = len(next(iter(polynomial.terms)))

    def gen_boolean_points(self, n: int) -> list[tuple[int, ...]]:
        """Generate all points in {0,1}^n."""
        return list(itertools.product([0, 1], repeat=n))

    def calc_total_sum(self) -> int:
        """Calculate the sum of f over the Boolean hypercube."""
        return self.f.reduce(
            sum(
                self.f.evaluate(point)
                for point in self.gen_boolean_points(self.n)
            )
        )

    def construct_round_polynomial(
        self,
        challenges: list[int]
    ) -> UnivariatePolynomial:
        """Construct the round polynomial for the current round.

        g_i(t) = sum f(r_1, ..., r_{i-1}, t, x_{i+1}, ..., x_n)
        """

        round_index = len(challenges)

        if round_index >= self.n:
            raise ValueError("Too many challenges.")

        fixed = [x % self.p for x in challenges]

        # Maximum degree in the current variable.
        max_degree = 0
        for exponents in self.f.terms:
            max_degree = max(max_degree, exponents[round_index])

        coefficients = [0] * (max_degree + 1)

        # Sum over all assignments to the remaining Boolean variables.
        remaining_indices = list(range(round_index + 1, self.n))

        for boolean_values in itertools.product(
            [0, 1],
            repeat=len(remaining_indices)
        ):
            point_base = [0] * self.n

            # Previously fixed challenges.
            for i, value in enumerate(fixed):
                point_base[i] = value

            # Remaining Boolean variables.
            for i, value in zip(remaining_indices, boolean_values):
                point_base[i] = value

            # Build the coefficient of t^degree term by term.
            for exponents, coefficient in self.f.terms.items():
                degree = exponents[round_index]

                term = coefficient % self.p

                # Variables before the current variable.
                for i in range(round_index):
                    term *= pow(
                        point_base[i] % self.p,
                        exponents[i],
                        self.p
                    )
                    term %= self.p

                # Variables after the current variable.
                for i in remaining_indices:
                    term *= pow(
                        point_base[i] % self.p,
                        exponents[i],
                        self.p
                    )
                    term %= self.p

                coefficients[degree] += term
                coefficients[degree] %= self.p

        return UnivariatePolynomial(coefficients, self.p)

    def prove(
        self,
        challenges: list[int] | None = None
    ) -> list[tuple[UnivariatePolynomial, int]]:
        """Generate a complete SumCheck proof."""

        if challenges is None:
            challenges = [
                random.randrange(self.p)
                for _ in range(self.n)
            ]
        else:
            if len(challenges) != self.n:
                raise ValueError(
                    f"Expected {self.n} challenges, got {len(challenges)}."
                )
            challenges = [x % self.p for x in challenges]

        proof = []
        previous_challenges = []

        for i in range(self.n):
            round_polynomial = self.construct_round_polynomial(
                previous_challenges
            )

            challenge = challenges[i]

            proof.append((round_polynomial, challenge))
            previous_challenges.append(challenge)

        return proof

    def verify(
        self,
        claimed_sum: int,
        proof: list[tuple[UnivariatePolynomial, int]]
    ) -> bool:
        """Verify a complete SumCheck proof."""

        try:
            if len(proof) != self.n:
                return False

            current_sum = claimed_sum % self.p
            challenges = []

            for round_polynomial, challenge in proof:
                if not isinstance(round_polynomial, UnivariatePolynomial):
                    return False

                challenge %= self.p

                # SumCheck consistency condition:
                # g_i(0) + g_i(1) == previous claimed sum
                left = (
                    round_polynomial.evaluate(0)
                    + round_polynomial.evaluate(1)
                ) % self.p

                if left != current_sum:
                    return False

                # The verifier evaluates g_i at the random challenge.
                current_sum = round_polynomial.evaluate(challenge)
                challenges.append(challenge)

            # Final claimed value must equal
            # f(r_1, ..., r_n).
            final_value = self.f.evaluate(tuple(challenges))

            return current_sum % self.p == final_value % self.p

        except (TypeError, ValueError, KeyError, StopIteration):
            return False


if __name__ == "__main__":
    # f = x*y + x + 2
    polynomial = Polynomial(
        terms={
            (1, 1): 1,
            (1, 0): 1,
            (0, 0): 2
        },
        p=17
    )

    sc = SumCheck(polynomial=polynomial)

    claimed_sum = sc.calc_total_sum()

    proof = sc.prove(
        challenges=[3, 5]
    )

    print("Claimed sum:", claimed_sum)
    print("Proof verified?:", sc.verify(claimed_sum, proof))
