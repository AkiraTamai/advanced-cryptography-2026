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
        """Initializes `Polynomial` instance.

        Args:
            terms: terms of a polynomial
            p: order of finite field (a prime number)

        Returns:
            None
        """
        self.terms = terms
        self.p = p

    def reduce(self, x: int) -> int:
        """Calculates x (mod p).

        Args:
            x: target number

        Returns:
            x (mod p)
        """
        return x % self.p

    def evaluate(self, point: tuple[int, ...]) -> int:
        """Evaluates polynomial at `point`.

        Args:
            point: evaluation point

        Returns:
            Evaluation result
        """
        total = 0

        for exponents, coefficient in self.terms.items():
            term_value = coefficient

            for exponent, value in zip(exponents, point):
                term_value *= value ** exponent

            total += term_value

        return self.reduce(total)


class UnivariatePolynomial(Polynomial):
    """Class representing a univariate polynomial.

    terms: coefficients of a univariate polynomial
    p: order of finite field (a prime number)

    e.g.)
        [c_0, c_, ..., c_d] = c_0 + c_*x + ... + c_d*x^d
    """
    def __init__(
        self,
        coefficients: list[int],
        p: int
    ) -> None:
        """Initializes `UnivariatePolynomial` instance.

        Args:
            coefficients: coefficients of a univariate polynomial
            p: order of finite field (a prime number)

        Returns:
            None
        """
        self.coefficients = coefficients
        self.p = p

    def evaluate(self, x: int) -> int:
        """Evaluates polynomial at `x`.

        Args:
            x: evaluation point

        Returns:
            Evaluation result
        """
        total = 0

        for exponent, coefficient in enumerate(self.coefficients):
            total += coefficient * x ** exponent

        return self.reduce(total)


class SumCheck:
    """Class representing SumCheck protocol.

    f: target function (i.e., polynomial or computation)
    p: order of finite field of `f`
    n: number of variables of `f`
    """

    def __init__(
        self,
        polynomial: Polynomial
    ) -> None:
        """Initializes `SumCheck` instance.

        Args:
            polynomial: target polynomial

        Returns:
            None
        """
        self.f = polynomial
        self.p = polynomial.p
        self.n = len(next(iter(polynomial.terms)))

    def gen_boolean_points(self, n: int) -> list[tuple[int, ...]]:
        """Generates all the combinations of {0,1}^n.

        Args:
            n: bit length

        Returns:
            A set of all the vertices of n-dimensional boolean hypercube
        """
        return itertools.product([0, 1], repeat=n)

    def calc_total_sum(self) -> int:
        """Calculates Σf(x), ∀x ∈ {0,1}^n.

        Args:
            None

        Returns:
            Total sum
        """
        return self.f.reduce(
            sum(self.f.evaluate(point) for point in self.gen_boolean_points(self.n))
        )

    def construct_round_polynomial(self, challenges: list[int]) -> UnivariatePolynomial:
        """Constructs the round polynomial g_i(t) = Σf(r_1, ..., r_{i-1}, t, x_{i+1}, ..., x_n).

        Args:
            challenges: fixed random challenge values

        Returns:
            Univariate polynomial for a single round
        """
        variable_index = len(challenges)
        degree = max(exponents[variable_index] for exponents in self.f.terms)
        coefficients = [0] * (degree + 1)
        remaining_variables = self.n - variable_index - 1

        for boolean_point in self.gen_boolean_points(remaining_variables):
            for exponents, coefficient in self.f.terms.items():
                term_coefficient = coefficient

                for index, challenge in enumerate(challenges):
                    term_coefficient *= challenge ** exponents[index]

                for offset, value in enumerate(boolean_point, start=variable_index + 1):
                    term_coefficient *= value ** exponents[offset]

                current_exponent = exponents[variable_index]
                coefficients[current_exponent] += term_coefficient

        return UnivariatePolynomial(
            coefficients=[self.f.reduce(value) for value in coefficients],
            p=self.p,
        )

    def prove(self, challenges:list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values

        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        if challenges is not None and len(challenges) != self.n:
            raise ValueError("The number of challenges must match the number of variables.")

        proof = []
        round_challenges = []

        for round_index in range(self.n):
            round_polynomial = self.construct_round_polynomial(round_challenges)

            if challenges is None:
                challenge = random.randrange(self.p)
            else:
                challenge = challenges[round_index] % self.p

            proof.append((round_polynomial, challenge))
            round_challenges.append(challenge)

        return proof

    def verify(
        self,
        claimed_sum: int,
        proof: list[tuple[UnivariatePolynomial, int]]
    ) -> bool:
        """Verifies a proof.

        Args:
            claimed_sum: Claimed sum of target function
            proof: proof of the claimed sum

        Returns:
            True if succeeded, false otherwise
        """
        if len(proof) != self.n:
            return False

        expected_value = self.f.reduce(claimed_sum)
        challenges = []

        for round_index, (round_polynomial, challenge) in enumerate(proof):
            if round_polynomial.p != self.p:
                return False

            max_degree = max(
                exponents[round_index] for exponents in self.f.terms
            )
            if len(round_polynomial.coefficients) > max_degree + 1:
                return False

            round_sum = self.f.reduce(
                round_polynomial.evaluate(0) + round_polynomial.evaluate(1)
            )
            if round_sum != expected_value:
                return False

            challenge = challenge % self.p
            expected_value = round_polynomial.evaluate(challenge)
            challenges.append(challenge)

        return expected_value == self.f.evaluate(tuple(challenges))


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

    # f([0, 0]) + f([0, 1]) + f([1, 0]) + f([1, 0])
    claimed_sum = sc.calc_total_sum()

    proof = sc.prove(
        challenges=[3, 5]
    )

    print("Claimed sum:", claimed_sum)
    print("Proof verified?:", sc.verify(claimed_sum, proof))
