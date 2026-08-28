import itertools
import random
import math


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
        return sum(
            [
                coefficient * math.prod([pow(v, exponent, self.p) for v, exponent in zip(point, exponents)])
                for (exponents, coefficient) in self.terms.items()
            ]
        ) % self.p


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
        return sum(
            [coefficient * pow(x, i, self.p) for i, coefficient in enumerate(self.coefficients)] 
        ) % self.p


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
        current_variable_index = len(challenges)
        max_degree = max(
            exponents[current_variable_index]
            for exponents in self.f.terms
        )
        # 係数は最大次数分必要
        coefficients = [0 for _ in range(max_degree + 1)]
        for exponents, coefficient in self.f.terms.items():
            # challenge部の計算
            challenge_value = 1
            for i, challenge in enumerate(challenges):
                challenge_value *= pow(challenge, exponents[i])

            # boolean変数部の計算
            boolean_value = 1
            for exponent in exponents[current_variable_index + 1:]:
                if exponent == 0:
                    boolean_value *= 2

            # このexponentの係数に加える
            current_exponent = exponents[current_variable_index]
            coefficients[current_exponent] = (coefficients[current_exponent] + challenge_value * boolean_value * coefficient) % self.p

        return UnivariatePolynomial(
            coefficients,
            self.p
        )

    def prove(self, challenges:list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values
        
        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        current_challenges = []
        proves = []
        for i in range(self.n):
            g = self.construct_round_polynomial(current_challenges)
            current_challenge = challenges[i] if challenges is not None else random.randint(0, self.p - 1)
            current_challenges.append(current_challenge)
            proves.append((g, current_challenge))
        return proves

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
        random_values = []
        # 次ラウンドの期待値を保持しておく
        expected_value = claimed_sum % self.p

        for g, r in proof:
            if expected_value != sum([g.evaluate(b) for b in [0, 1]]) % self.p:
                return False

            expected_value = g.evaluate(r) % self.p
            random_values.append(r)
            
        if expected_value != self.f.evaluate(random_values):
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
