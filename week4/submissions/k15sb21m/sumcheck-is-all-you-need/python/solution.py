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
            # 各項は coef * x_1^e_1 * ... * x_n^e_n
            monomial = coefficient
            for value, exponent in zip(point, exponents):
                monomial *= pow(value, exponent, self.p)
            total += monomial
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
        for degree, coefficient in enumerate(self.coefficients):
            total += coefficient * pow(x, degree, self.p)
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
        # 今回のラウンドで自由変数として残す変数の位置（0-indexed）
        index = len(challenges)
        # 残りの変数（x_{i+1}, ..., x_n）の個数
        remaining = self.n - index - 1

        # t の最大次数（= f における変数 index の最大次数）
        degree = max(exponents[index] for exponents in self.f.terms)
        coefficients = [0] * (degree + 1)

        # 後ろの変数を {0,1} で全通り走査し、t の各次数の係数を集める
        for tail in self.gen_boolean_points(remaining):
            for exponents, coefficient in self.f.terms.items():
                monomial = coefficient
                # 確定済みのチャレンジ r_1, ..., r_{i-1} を代入
                for value, exponent in zip(challenges, exponents[:index]):
                    monomial *= pow(value, exponent, self.p)
                # 残りの変数に 0/1 を代入
                for value, exponent in zip(tail, exponents[index + 1:]):
                    monomial *= pow(value, exponent, self.p)
                # 変数 index の次数の係数として足し込む
                power = exponents[index]
                coefficients[power] = (coefficients[power] + monomial) % self.p

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

        for i in range(self.n):
            # ラウンド i の一変数多項式 g_i(t)
            round_polynomial = self.construct_round_polynomial(fixed)

            # チャレンジ r_i（指定がなければランダムに選ぶ）
            if challenges is not None and i < len(challenges):
                challenge = challenges[i] % self.p
            else:
                challenge = random.randrange(self.p)

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
        # ラウンド数が変数の数と一致しない証明は不正
        if len(proof) != self.n:
            return False

        expected = claimed_sum % self.p
        challenges: list[int] = []

        for round_polynomial, challenge in proof:
            # g_i(0) + g_i(1) が、直前のラウンドから受け継いだ値と一致するか
            if (round_polynomial.evaluate(0) + round_polynomial.evaluate(1)) % self.p != expected:
                return False
            # 次のラウンドへ渡す値は g_i(r_i)
            expected = round_polynomial.evaluate(challenge)
            challenges.append(challenge)

        # 最後は f 自身を全チャレンジ点で評価して突き合わせる
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