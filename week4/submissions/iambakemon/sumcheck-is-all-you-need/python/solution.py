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
            term = coefficient
            # zip pairs each variable with its exponent; pow(..., self.p) keeps
            # intermediates small and gives 0**0 == 1, which the constant term
            # relies on.
            for value, exponent in zip(point, exponents):
                term *= pow(value, exponent, self.p)
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
        # Horner's method: c_0 + x*(c_1 + x*(c_2 + ...)). Reducing inside the
        # loop keeps the running value bounded by p instead of x**d.
        result = 0
        for coefficient in reversed(self.coefficients):
            result = self.reduce(result * x + coefficient)
        return result


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
        # The round index is implied by how many challenges are already fixed.
        index = len(challenges)
        degree = max(exponents[index] for exponents in self.f.terms)
        coefficients = [0] * (degree + 1)

        for exponents, coefficient in self.f.terms.items():
            weight = coefficient
            # Variables before the current one are bound to past challenges.
            # zip stops at the shorter sequence, so it covers exactly those.
            for value, exponent in zip(challenges, exponents):
                weight *= pow(value, exponent, self.p)
            # Variables after it are still summed over {0,1}. The sum
            # factorises per variable, and Σ_{b∈{0,1}} b**e is 2 for e == 0
            # (0**0 == 1) and 1 otherwise -- so no hypercube walk is needed.
            for exponent in exponents[index + 1:]:
                if exponent == 0:
                    weight *= 2
            # Terms sharing an exponent on the current variable collapse into
            # the same coefficient of t.
            coefficients[exponents[index]] = self.f.reduce(
                coefficients[exponents[index]] + weight
            )

        return UnivariatePolynomial(coefficients, self.p)

    def prove(self, challenges:list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values
        
        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        proof: list[tuple[UnivariatePolynomial, int]] = []
        fixed: list[int] = []
        for round_index in range(self.n):
            # Round i only depends on the challenges of rounds 1..i-1.
            round_polynomial = self.construct_round_polynomial(fixed)
            if challenges is None:
                challenge = random.randrange(self.p)
            else:
                challenge = challenges[round_index]
            proof.append((round_polynomial, challenge))
            fixed.append(challenge)
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
        challenges: list[int] = []
        for round_polynomial, challenge in proof:
            # Each round reduces "the sum over the remaining hypercube equals
            # `expected`" to the same claim with one fewer variable.
            consistency = round_polynomial.evaluate(0) + round_polynomial.evaluate(1)
            if self.f.reduce(consistency) != expected:
                return False
            expected = round_polynomial.evaluate(challenge)
            challenges.append(challenge)

        # The recursion bottoms out here: the last claim is about a single
        # point, which the verifier can check against f directly. Skipping this
        # makes every proof pass, since the rounds only relate g_i to g_{i+1}.
        return self.f.evaluate(tuple(challenges)) == expected


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
