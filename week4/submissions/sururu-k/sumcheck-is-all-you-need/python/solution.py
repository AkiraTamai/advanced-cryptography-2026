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
        res = 0
        for exp, coef in self.terms.items():
            term_val = coef
            for x, e in zip(point, exp):
                if e > 0:
                    term_val = (term_val * pow(x, e, self.p)) % self.p
            res = (res + term_val) % self.p
        return res


class UnivariatePolynomial(Polynomial):
    """Class representing a univariate polynomial.

    terms: coefficients of a univariate polynomial
    p: order of finite field (a prime number)

    e.g.)
        [c_0, c_1, ..., c_d] = c_0 + c_1*x + ... + c_d*x^d
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
        self.coefficients = [c % p for c in coefficients]
        self.p = p

    def evaluate(self, x: int) -> int:
        """Evaluates polynomial at `x`.

        Args:
            x: evaluation point
        
        Returns:
            Evaluation result
        """
        res = 0
        for deg, coef in enumerate(self.coefficients):
            res = (res + coef * pow(x, deg, self.p)) % self.p
        return res


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
        return list(itertools.product([0, 1], repeat=n))

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
            challenges: fixed random challenge values (r_1, ..., r_{i-1})
        
        Returns:
            Univariate polynomial for a single round
        """
        i = len(challenges)  # 0-indexed current round
        rem_vars = self.n - 1 - i
        bool_points = self.gen_boolean_points(rem_vars)

        # Find maximum degree of t (i-th variable)
        max_deg = 0
        for exp in self.f.terms.keys():
            if exp[i] > max_deg:
                max_deg = exp[i]

        poly_coeffs = [0] * (max_deg + 1)
        for bool_pt in bool_points:
            for exp, coef in self.f.terms.items():
                deg_t = exp[i]
                term_val = coef
                # Prefix evaluated with challenges
                for r, e in zip(challenges, exp[:i]):
                    if e > 0:
                        term_val = (term_val * pow(r, e, self.p)) % self.p
                # Suffix evaluated with boolean point
                for x, e in zip(bool_pt, exp[i + 1:]):
                    if e > 0:
                        term_val = (term_val * pow(x, e, self.p)) % self.p
                poly_coeffs[deg_t] = (poly_coeffs[deg_t] + term_val) % self.p

        return UnivariatePolynomial(poly_coeffs, self.p)

    def prove(self, challenges: list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values
        
        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        if challenges is None:
            challenges = [random.randint(0, self.p - 1) for _ in range(self.n)]

        proof = []
        current_challenges: list[int] = []
        for r_i in challenges:
            g_i = self.construct_round_polynomial(current_challenges)
            proof.append((g_i, r_i))
            current_challenges.append(r_i)

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

        current_target = claimed_sum % self.p
        challenges: list[int] = []

        for g_i, r_i in proof:
            # Check g_i(0) + g_i(1) == current_target (mod p)
            if (g_i.evaluate(0) + g_i.evaluate(1)) % self.p != current_target:
                return False
            challenges.append(r_i)
            current_target = g_i.evaluate(r_i)

        # Final check: g_n(r_n) == f(r_1, ..., r_n) (mod p)
        if self.f.evaluate(tuple(challenges)) != current_target:
            return False

        return True


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
