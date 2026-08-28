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
            # 指数ベクトルと評価点の長さが違うと、どの変数に値を代入するか
            # 一意に決まらないため、zip で黙って切り捨てず明示的に失敗させる。
            if len(exponents) != len(point):
                raise ValueError(
                    "The dimension of point must match the polynomial."
                )

            # 各単項式 c * x_1^e_1 * ... * x_n^e_n を有限体 F_p 上で
            # 評価する。途中でも剰余を取ることで、不要に大きな整数を作らない。
            term_value = self.reduce(coefficient)
            for value, exponent in zip(point, exponents):
                if exponent < 0:
                    raise ValueError("Polynomial exponents must be non-negative.")
                term_value = self.reduce(
                    term_value * pow(self.reduce(value), exponent, self.p)
                )

            result = self.reduce(result + term_value)

        return result


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
        # Horner 法を使うと、次数 d の多項式を d 回の乗算で評価できる。
        # 例: c_0 + c_1*x + c_2*x^2 = ((c_2*x) + c_1)*x + c_0
        x = self.reduce(x)
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
        # challenges の個数が、これまでに値を固定した変数の個数に等しい。
        # したがって、このラウンドで形式変数 t に置き換えるのは x_i である。
        round_index = len(challenges)
        if round_index >= self.n:
            raise ValueError("Too many challenges for a SumCheck round.")

        # g_i の次数は、元の多項式 f の変数 x_i に関する次数以下になる。
        # 途中で最高次係数が 0 になっても、係数リストの長さを一定に保つ。
        degree = 0
        for exponents in self.f.terms:
            if len(exponents) != self.n:
                raise ValueError(
                    "All terms must have the same number of variables."
                )
            if any(exponent < 0 for exponent in exponents):
                raise ValueError("Polynomial exponents must be non-negative.")
            degree = max(degree, exponents[round_index])

        coefficients = [0] * (degree + 1)

        for exponents, coefficient in self.f.terms.items():
            # まず、既に検証者が選んだ r_1, ..., r_{i-1} を代入する。
            fixed_coefficient = self.f.reduce(coefficient)
            for variable_index, challenge in enumerate(challenges):
                fixed_coefficient = self.f.reduce(
                    fixed_coefficient
                    * pow(
                        self.f.reduce(challenge),
                        exponents[variable_index],
                        self.p,
                    )
                )

            # 残りの各変数について {0, 1} 上の和を取る。
            # 指数 e が 0 なら 0^0 + 1^0 = 2、e > 0 なら
            # 0^e + 1^e = 1 なので、全点を列挙せず積として計算できる。
            for exponent in exponents[round_index + 1:]:
                if exponent == 0:
                    fixed_coefficient = self.f.reduce(2 * fixed_coefficient)

            t_degree = exponents[round_index]
            coefficients[t_degree] = self.f.reduce(
                coefficients[t_degree] + fixed_coefficient
            )

        return UnivariatePolynomial(coefficients, self.p)

    def prove(
        self,
        challenges: list[int] | None = None
    ) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values
        
        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        if challenges is None:
            # F_p の要素は 0, ..., p-1 のいずれかとして表現する。
            round_challenges = [random.randrange(self.p) for _ in range(self.n)]
        else:
            if len(challenges) != self.n:
                raise ValueError(
                    f"Expected {self.n} challenges, got {len(challenges)}."
                )
            # 同じ有限体要素に複数の整数表現を残さないよう正規化する。
            round_challenges = [self.f.reduce(value) for value in challenges]

        proof = []
        for round_index, challenge in enumerate(round_challenges):
            # 第 i ラウンドの g_i は、それ以前のチャレンジだけを固定して作る。
            round_polynomial = self.construct_round_polynomial(
                round_challenges[:round_index]
            )
            proof.append((round_polynomial, challenge))

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
        # n 変数の SumCheck では、各変数につき必ず 1 ラウンド必要になる。
        if not isinstance(claimed_sum, int):
            return False
        try:
            if len(proof) != self.n:
                return False
            expected_value = self.f.reduce(claimed_sum)
        except (TypeError, ValueError):
            return False

        challenges = []

        for round_index, round_data in enumerate(proof):
            try:
                round_polynomial, challenge = round_data
            except (TypeError, ValueError):
                return False

            if not isinstance(round_polynomial, UnivariatePolynomial):
                return False
            if round_polynomial.p != self.p:
                return False
            if not isinstance(round_polynomial.coefficients, list):
                return False
            if not all(
                isinstance(coefficient, int)
                for coefficient in round_polynomial.coefficients
            ):
                return False
            if not isinstance(challenge, int):
                return False

            try:
                # SumCheck の健全性には、証明者が元の f より高い次数の
                # g_i を送り込めないことも必要である。F_p 上で 0 になる
                # 末尾係数は次数に数えず、同じ多項式の表現は受理する。
                degree_bound = max(
                    exponents[round_index] for exponents in self.f.terms
                )
                actual_degree = -1
                for coefficient_index in range(
                    len(round_polynomial.coefficients) - 1,
                    -1,
                    -1,
                ):
                    if self.f.reduce(
                        round_polynomial.coefficients[coefficient_index]
                    ) != 0:
                        actual_degree = coefficient_index
                        break
                if actual_degree > degree_bound:
                    return False

                # 第 1 ラウンドでは g_1(0)+g_1(1) が claimed_sum と一致する。
                # 以後は g_i(0)+g_i(1) が直前の g_{i-1}(r_{i-1}) と
                # 一致することを検査し、各ラウンドを一本の主張につなげる。
                boolean_sum = self.f.reduce(
                    round_polynomial.evaluate(0)
                    + round_polynomial.evaluate(1)
                )
                if boolean_sum != expected_value:
                    return False

                challenge = self.f.reduce(challenge)
                expected_value = round_polynomial.evaluate(challenge)
            except (TypeError, ValueError):
                return False

            challenges.append(challenge)

        # 最終ラウンドの主張 g_n(r_n) は、検証者が直接計算できる
        # f(r_1, ..., r_n) と一致しなければならない。
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

    # f([0, 0]) + f([0, 1]) + f([1, 0]) + f([1, 1])
    claimed_sum = sc.calc_total_sum()

    proof = sc.prove(
        challenges=[3, 5]
    )

    print("Claimed sum:", claimed_sum)
    print("Proof verified?:", sc.verify(claimed_sum, proof))
