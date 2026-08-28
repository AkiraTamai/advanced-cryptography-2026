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
        result = 0
        for exponents, coefficient in self.terms.items():
            monomial = coefficient
            for value, exponent in zip(point, exponents):
                monomial *= pow(value, exponent, self.p)
            result += monomial
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
        for exponent, coefficient in enumerate(self.coefficients):
            result += coefficient * pow(x, exponent, self.p)
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

    def degree_of(self, i: int) -> int:
        """Calculates the degree of `f` in its i-th variable (0-based).

        Args:
            i: index of the variable

        Returns:
            Highest exponent of x_i appearing in `f`
        """
        return max(exponents[i] for exponents in self.f.terms)

    def construct_round_polynomial(self, challenges: list[int]) -> UnivariatePolynomial:
        """Constructs the round polynomial g_i(t) = Σf(r_1, ..., r_{i-1}, t, x_{i+1}, ..., x_n).

        Args:
            challenges: fixed random challenge values
        
        Returns:
            Univariate polynomial for a single round
        """
        # Index of the variable left free as `t` in this round (0-based)
        i = len(challenges)

        coefficients = [0] * (self.degree_of(i) + 1)

        for exponents, coefficient in self.f.terms.items():
            term = coefficient

            # x_1, ..., x_{i-1} are already fixed to the challenge values
            for value, exponent in zip(challenges, exponents):
                term *= pow(value, exponent, self.p)

            # x_{i+1}, ..., x_n are summed over {0,1}.
            # Σ_{x ∈ {0,1}} x^e is 2 when e == 0 (constant) and 0^e + 1^e = 1 otherwise.
            for exponent in exponents[i + 1:]:
                if exponent == 0:
                    term *= 2

            # x_i^e contributes to the coefficient of t^e
            coefficients[exponents[i]] += term

        return UnivariatePolynomial(
            coefficients=[self.f.reduce(c) for c in coefficients],
            p=self.p
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

        proof = []
        for i in range(self.n):
            # g_i(t) only depends on the challenges of the previous rounds
            round_polynomial = self.construct_round_polynomial(challenges[:i])
            proof.append((round_polynomial, challenges[i]))

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

        # The value the current round has to reconcile with
        expected = self.f.reduce(claimed_sum)
        challenges = []

        for i, (round_polynomial, challenge) in enumerate(proof):
            # g_i(t) must not have a higher degree than x_i has in f
            if len(round_polynomial.coefficients) > self.degree_of(i) + 1:
                return False

            # g_i(0) + g_i(1) must reproduce the sum claimed before this round
            round_sum = round_polynomial.evaluate(0) + round_polynomial.evaluate(1)
            if self.f.reduce(round_sum) != expected:
                return False

            # The next round has to prove g_i(r_i)
            expected = round_polynomial.evaluate(challenge)
            challenges.append(challenge)

        # Last round: check the remaining claim against f with a single evaluation
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
