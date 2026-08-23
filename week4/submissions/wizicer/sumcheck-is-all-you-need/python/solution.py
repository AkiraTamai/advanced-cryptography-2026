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
        if len(point) != len(next(iter(self.terms))):
            raise ValueError("point dimension must match polynomial dimension")

        result = 0
        for exponents, coefficient in self.terms.items():
            term = coefficient
            for value, exponent in zip(point, exponents):
                term *= pow(value, exponent, self.p)
            result += term
        return self.reduce(result)


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
        result = 0
        for coefficient in reversed(self.coefficients):
            result = result * x + coefficient
        return self.reduce(result)


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
        round_index = len(challenges)
        if round_index >= self.n:
            raise ValueError("too many fixed challenges")

        degree = max(exponents[round_index] for exponents in self.f.terms)
        coefficients = [0] * (degree + 1)
        remaining_variables = self.n - round_index - 1

        # 1. precompile challenges
        prefix_contributions = {}
        for exponents, coefficient in self.f.terms.items():
            prefix = coefficient
            for val, exp in zip(challenges, exponents[:round_index]):
                prefix *= pow(val, exp, self.p)
            prefix_contributions[exponents] = prefix

        # 2. iterate boolean_suffix and calculate suffix part
        for boolean_suffix in self.gen_boolean_points(remaining_variables):
            for exponents, prefix in prefix_contributions.items():
                contribution = prefix
                for val, exp in zip(boolean_suffix, exponents[round_index + 1:]):
                    contribution *= pow(val, exp, self.p)

                current_exponent = exponents[round_index]
                coefficients[current_exponent] += contribution

        return UnivariatePolynomial(
            [self.f.reduce(value) for value in coefficients],
            self.p,
        )

    def prove(self, challenges:list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values

        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        if challenges is None:
            challenges = [random.randrange(self.p) for _ in range(self.n)]
        if len(challenges) != self.n:
            raise ValueError("the proof needs one challenge per round")

        proof = []
        fixed_challenges = []
        for challenge in challenges:
            round_polynomial = self.construct_round_polynomial(fixed_challenges)
            reduced_challenge = self.f.reduce(challenge)
            proof.append((round_polynomial, reduced_challenge))
            fixed_challenges.append(reduced_challenge)
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

        expected = self.f.reduce(claimed_sum)
        challenges = []

        for round_index, proof_item in enumerate(proof):
            if len(proof_item) != 2:
                return False
            round_polynomial, challenge = proof_item
            if not isinstance(round_polynomial, UnivariatePolynomial):
                return False
            if round_polynomial.p != self.p:
                return False

            max_degree = max(
                exponents[round_index] for exponents in self.f.terms
            )
            actual_degree = max(
                (
                    index
                    for index, coefficient in enumerate(
                        round_polynomial.coefficients
                    )
                    if coefficient % self.p != 0
                ),
                default=0,
            )
            if actual_degree > max_degree:
                return False

            round_sum = self.f.reduce(
                round_polynomial.evaluate(0)
                + round_polynomial.evaluate(1)
            )
            if round_sum != expected:
                return False

            challenge = self.f.reduce(challenge)
            challenges.append(challenge)
            expected = round_polynomial.evaluate(challenge)

        return expected == self.f.evaluate(tuple(challenges))


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
