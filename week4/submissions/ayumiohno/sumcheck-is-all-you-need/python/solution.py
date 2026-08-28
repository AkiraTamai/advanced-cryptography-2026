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
        for exps, coef in self.terms.items():
            term = coef
            for exp, x in zip(exps, point):
                term = self.reduce(term * pow(x, exp, self.p))
            total = self.reduce(total + term)
        return total
        # raise NotImplementedError("Please implement this method.")


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
        for i in range(len(self.coefficients)):
            total = self.reduce(total + self.coefficients[i] * pow(x, i, self.p))
        return total
        # raise NotImplementedError("Please implement this method.")


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
        i = len(challenges)
        deg = max(exps[i] for exps in self.f.terms)
        coefficients = [0] * (deg + 1)
        for b in self.gen_boolean_points(self.n - i - 1):
            # Construct the point (r_1, ..., r_{i-1}, t, x_{i+1}, ..., x_n)
            point = challenges + [0] + list(b)
            for exps, coef in self.f.terms.items():
                value = coef
                for j, exp in enumerate(exps):
                    if j == i:
                        continue
                    value = self.f.reduce(value * pow(point[j], exp, self.p))
                coefficients[exps[i]] = self.f.reduce(coefficients[exps[i]] + value)
        return UnivariatePolynomial(coefficients=coefficients, p=self.p)
        # raise NotImplementedError("Please implement this method.")

    def prove(self, challenges:list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values
        
        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        proof = []
        fixed_challenges = []
        for i in range(self.n):
            g_i = self.construct_round_polynomial(fixed_challenges)
            r_i = random.randint(0, self.p - 1) if challenges is None else challenges[i]
            proof.append((g_i, r_i))
            fixed_challenges.append(r_i)
        return proof
        # raise NotImplementedError("Please implement this method.")

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
        expected = self.f.reduce(claimed_sum)
        rs = []
        for i, (g_i, r_i) in enumerate(proof):
            # Check if g_i(0) + g_i(1) == expected
            if self.f.reduce(g_i.evaluate(0) + g_i.evaluate(1)) != expected:
                return False
            # Update expected for the next round
            expected = g_i.evaluate(r_i)
            rs.append(r_i)
        return self.f.reduce(expected) == self.f.evaluate(tuple(rs))
        # raise NotImplementedError("Please implement this method.")


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
