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
        for powers, coefficient in self.terms.items():
            term = coefficient
            for x, power in zip(point, powers):
                term *= pow(x, power)
            total += term

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
        for power, coefficient in enumerate(self.coefficients):
            total += coefficient * pow(x, power)

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
        round_index = len(challenges)
        if round_index >= self.n:
            raise ValueError("too many challenges")

        max_degree = max(powers[round_index] for powers in self.f.terms)
        coefficients = [0] * (max_degree + 1)
        remaining_variables = self.n - round_index - 1

        for suffix in self.gen_boolean_points(remaining_variables):
            for powers, coefficient in self.f.terms.items():
                term = coefficient

                for challenge, power in zip(challenges, powers[:round_index]):
                    term *= pow(challenge, power)

                for x, power in zip(suffix, powers[round_index + 1:]):
                    term *= pow(x, power)

                coefficients[powers[round_index]] += term

        return UnivariatePolynomial(
            [self.f.reduce(coefficient) for coefficient in coefficients],
            self.p
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
            raise ValueError("number of challenges must match number of variables")

        proof = []
        for i, challenge in enumerate(challenges):
            round_polynomial = self.construct_round_polynomial(challenges[:i])
            proof.append((round_polynomial, self.f.reduce(challenge)))

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

        expected_sum = self.f.reduce(claimed_sum)
        challenges = []

        for round_polynomial, challenge in proof:
            if round_polynomial.p != self.p:
                return False
            if self.f.reduce(round_polynomial.evaluate(0) + round_polynomial.evaluate(1)) != expected_sum:
                return False

            challenge = self.f.reduce(challenge)
            challenges.append(challenge)
            expected_sum = round_polynomial.evaluate(challenge)

        return expected_sum == self.f.evaluate(tuple(challenges))


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
