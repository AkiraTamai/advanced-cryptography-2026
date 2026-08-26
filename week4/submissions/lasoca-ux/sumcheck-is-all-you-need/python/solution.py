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
            多変数多項式の各変数に代入する値
        
        Returns:
            Evaluation result
        """
        # 指数のタプルには、変数ごとに1つの指数が入っている
        for exponents in self.terms:
            if len(exponents) != len(point):
                # 評価点の要素数が一致しない場合は、呼び出し側の誤りとする
                raise ValueError("評価点の要素数が変数の数と一致しません。")

        result = 0

        for exponents, coefficient in self.terms.items():
            term_value = coefficient
            for variable_value, exponent in zip(point, exponents):
                #variable_value の exponent 乗を計算しself.p で割った余りを求める
                #variable_value：底。多項式の変数に代入された値
                #exponent：指数。何乗するか
                #self.p：法。計算結果を割る数
                term_value *= pow(variable_value, exponent, self.p)
                term_value %= self.p
            result += term_value
            result %= self.p

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
        #ホーナー法を使い、xの各べき乗を個別に計算せず多項式を評価
        result = 0
        #self.coefficients：一変数多項式の各次数の係数リスト
        for coefficient in reversed(self.coefficients):
            result = (result * x + coefficient) % self.p
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
        #challenges：それまでのラウンドで決まったチャレンジ値のリスト
        #self.n：元の多変数多項式に含まれる変数の数
        round_index = len(challenges)
        if round_index >= self.n:
            raise ValueError("ラウンド多項式の作成には、未確定の変数が1つ以上必要です。")

        #g_iの次数は、現在の変数に関するfの次数以下
        current_degree = max(exponents[round_index] for exponents in self.f.terms)
        coefficients = [0] * (current_degree + 1)
        remaining_variable_count = self.n - round_index - 1

        #tより後ろにある変数へ、すべての0・1の組み合わせを代入してfを合計
        #tの次数が同じ項は、同じ係数へまとめて加算する
        for boolean_values in self.gen_boolean_points(remaining_variable_count):
            for exponents, coefficient in self.f.terms.items():
                contribution = coefficient % self.p

                for index, challenge in enumerate(challenges):
                    contribution *= pow(challenge, exponents[index], self.p)
                    contribution %= self.p

                for offset, boolean_value in enumerate(boolean_values):
                    variable_index = round_index + 1 + offset
                    contribution *= pow(
                        boolean_value,
                        exponents[variable_index],
                        self.p
                    )
                    contribution %= self.p

                power_of_t = exponents[round_index]
                coefficients[power_of_t] += contribution
                coefficients[power_of_t] %= self.p

        #計算した係数を使って一変数多項式オブジェクトを作成
        return UnivariatePolynomial(coefficients, self.p)

    def prove(self, challenges:list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values
        
        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        if challenges is not None and len(challenges) != self.n:
            raise ValueError("各ラウンドにチャレンジ値を1つずつ指定してください。")

        proof = []
        selected_challenges = []
        for round_index in range(self.n):
            round_polynomial = self.construct_round_polynomial(selected_challenges)

            if challenges is None:
                challenge = random.randrange(self.p)
            else:
                challenge = challenges[round_index]

            #チャレンジ値は有限体の要素なので、pで割った余りに正規化して保存
            challenge %= self.p
            proof.append((round_polynomial, challenge))
            selected_challenges.append(challenge)

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

        expected_sum = claimed_sum % self.p
        challenges = []

        for round_index, (round_polynomial, challenge) in enumerate(proof):
            if not isinstance(round_polynomial, UnivariatePolynomial):
                return False
            if round_polynomial.p != self.p:
                return False

            #証明者が、このラウンドの変数に関するfの次数よりも
            #高い次数の多項式を使用していないことを確認
            allowed_degree = max(
                exponents[round_index] for exponents in self.f.terms
            )
            actual_degree = len(round_polynomial.coefficients) - 1
            while (
                actual_degree > 0
                and round_polynomial.coefficients[actual_degree] % self.p == 0
            ):
                actual_degree -= 1
            if actual_degree > allowed_degree:
                return False

            #SumCheckの整合性確認として、g_i(0) + g_i(1)が
            #前のラウンドから引き継いだ値と一致することを確認
            round_sum = (
                round_polynomial.evaluate(0) + round_polynomial.evaluate(1)
            ) % self.p
            if round_sum != expected_sum:
                return False

            challenge %= self.p
            expected_sum = round_polynomial.evaluate(challenge)
            challenges.append(challenge)

        #すべての変数を固定した後、最終ラウンドの値が
        #元の多変数多項式を直接評価した値と一致することを確認
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
