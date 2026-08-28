"""Week 4 課題「sumcheck-is-all-you-need」の解答ファイルです。

この課題で証明したい主張は、次のBoolean hypercube上の合計です。

    claimed_sum = Σ f(x_1, ..., x_n),  x_i in {0, 1}

SumCheckは、この大きな合計の主張を、1ラウンドにつき1変数ずつ
ランダムな値へ固定し、最後は元の多項式fの1点評価へ縮小します。

登場人物と、このファイルでの担当:
    証明者:
        construct_round_polynomial() で g_i(t) を作る
        prove() で全ラウンドの (g_i, r_i) を教材用proofにまとめる

    検証者:
        verify() で各ラウンドの主張がつながっているか確認する
        最後に f(r_1, ..., r_n) を1点だけ直接評価する

    両者が使える計算道具:
        Polynomial.evaluate() / UnivariatePolynomial.evaluate()

本物の対話型SumCheckでは、証明者がg_iを送った「後」に検証者がr_iを
選びます。この教材では通信を実装せず、対話の記録を
[(g_1, r_1), ..., (g_n, r_n)] としてまとめています。

例 f(x, y) = xy + x + 2, p=17:
    claimed_sum = 11
      == g_1(0) + g_1(1),  g_1(t) = 4 + 3t

    r_1 = 3 を選ぶ
    g_1(3) = 13
      == g_2(0) + g_2(1),  g_2(t) = 5 + 3t

    r_2 = 5 を選ぶ
    g_2(5) = 3
      == f(3, 5)

つまり、claimed_sum -> g_1 -> g_2 -> f という主張の鎖を検査します。
"""

from __future__ import annotations

import itertools
import random


# ======================================================= 多項式を評価する道具

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

        | 数学上の項 | xの指数 | yの指数 | 係数 | Python |
        |---|---:|---:|---:|---|
        | `xy` | 1 | 1 | 1 | `(1, 1): 1` |
        | `x` | 1 | 0 | 1 | `(1, 0): 1` |
        | `2` | 0 | 0 | 2 | `(0, 0): 2` |
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
        # terms のキーと point は、同じ位置同士が同じ変数を表す。
        #
        # 例: 項 {(1, 1): 1} と評価点 (3, 5) なら、
        #     係数 1 * 3**1 * 5**1 = 15
        #
        # キーに入っているのは「変数の値」ではなく「各変数の指数」。
        # point に入っているのが、実際に x, y, ... へ代入する値。
        number_of_variables = len(next(iter(self.terms)))
        if len(point) != number_of_variables:
            raise ValueError("point must contain one value for each variable")

        # 多項式全体の答えは、各項を評価した値の合計。
        evaluation_result = 0

        for exponents, coefficient in self.terms.items():
            if len(exponents) != number_of_variables:
                raise ValueError("all terms must use the same number of variables")

            # まず、その項の係数から始める。
            # 例: 2*x^3*y なら、最初は term_value = 2。
            term_value = coefficient

            for variable_value, exponent in zip(point, exponents):
                # 各変数について「代入値 ** 指数」を掛ける。
                # 0乗の項では Python も value**0 == 1 になるため、
                # その変数は項の値へ影響しない。
                term_value *= variable_value ** exponent

            # 1つの項の評価が終わったので、多項式全体の合計へ加える。
            evaluation_result += term_value

        # 多項式は有限体 F_p 上で計算するので、最後に mod p へ戻す。
        return self.reduce(evaluation_result)


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
        # coefficients のインデックスが次数を表す。
        # 例: [4, 3] は 4 + 3*x。
        evaluation_result = 0

        for degree, coefficient in enumerate(self.coefficients):
            evaluation_result += coefficient * (x ** degree)

        return self.reduce(evaluation_result)


# =========================================================== SumCheck本体

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
        # n=2 なら [(0,0), (0,1), (1,0), (1,1)]。
        # 「すべてのBoolean入力」を実際に目で追えるリストとして返す。
        return list(itertools.product([0, 1], repeat=n))

    def calc_total_sum(self) -> int:
        """Calculates Σf(x), ∀x ∈ {0,1}^n.

        Args:
            None

        Returns:
            Total sum
        """
        # これは正直なclaimed_sumを用意するための、証明者側の重い計算。
        # n=2なら4点、n=100なら2^100点を本当に列挙する。
        # SumCheckの検証者はこの全件計算をせず、verify()の最後に
        # ランダムな1点だけf.evaluate()する。
        boolean_points = self.gen_boolean_points(self.n)
        total_sum = 0

        for boolean_point in boolean_points:
            value_at_boolean_point = self.f.evaluate(boolean_point)
            total_sum += value_at_boolean_point

        return self.f.reduce(total_sum)

    def construct_round_polynomial(self, challenges: list[int]) -> UnivariatePolynomial:
        """Constructs the round polynomial g_i(t) = Σf(r_1, ..., r_{i-1}, t, x_{i+1}, ..., x_n).

        Args:
            challenges: fixed random challenge values

        Returns:
            Univariate polynomial for a single round
        """
        # -----------------------------------------------------------------
        # 1. 今回、どの変数を t として残すか決める
        # -----------------------------------------------------------------
        # challenges に入っているのは、これまでのラウンドで検証者が
        # 選んだ r_1, ..., r_{i-1}。その個数から、今回残す変数 i が決まる。
        #
        # 例: f(x, y) について
        #   challenges=[] なら x を t として残し、y=0,1 を足して g_1(t) を作る。
        #   challenges=[3] なら x=3 に固定し、y を t として残して g_2(t) を作る。
        variable_kept_as_t_index = len(challenges)

        if variable_kept_as_t_index >= self.n:
            raise ValueError("too many challenges for this polynomial")

        # -----------------------------------------------------------------
        # 2. g_i(t)の係数を入れる箱を用意する
        # -----------------------------------------------------------------
        # g_i(t) の係数リストは、今回残す変数の最大次数 + 1 個必要。
        # coefficients[k] が t**k の係数になる。
        variable_kept_as_t_max_degree = max(
            exponents[variable_kept_as_t_index]
            for exponents in self.f.terms
        )
        coefficients_by_t_degree = [
            0
        ] * (variable_kept_as_t_max_degree + 1)

        number_of_remaining_boolean_variables = (
            self.n - variable_kept_as_t_index - 1
        )

        remaining_boolean_points = self.gen_boolean_points(
            number_of_remaining_boolean_variables
        )

        # -----------------------------------------------------------------
        # 3. 数式 f(r_1, ..., r_{i-1}, t, x_{i+1}, ..., x_n) を作る
        # -----------------------------------------------------------------
        # 各ラウンドで変数は次の3状態に分かれる。
        #   challenges部分: すでにr_jへ固定済み
        #   None部分:       今回は値を入れず、tとして残す
        #   0/1部分:        まだ残っているので、全組み合わせについて足す
        #
        # f(x,y), challenges=[] なら:
        #   [None, 0], [None, 1]  -> f(t,0) + f(t,1) = g_1(t)
        #
        # f(x,y), challenges=[3] なら:
        #   [3, None]             -> f(3,t) = g_2(t)
        for remaining_boolean_point in remaining_boolean_points:
            values_with_t_placeholder = (
                list(challenges)
                + [None]
                + list(remaining_boolean_point)
            )

            for exponents, coefficient in self.f.terms.items():
                # 1つの項について、t以外の変数へ具体値を代入する。
                # tの場所だけは掛けず、その指数を係数の格納先に使う。
                coefficient_after_substitution = coefficient

                for variable_value, exponent in zip(
                    values_with_t_placeholder,
                    exponents,
                ):
                    if variable_value is None:
                        # この位置が今回残すt。値はまだ代入しない。
                        continue

                    coefficient_after_substitution *= (
                        variable_value ** exponent
                    )

                # 例: この項が「3*t^2」になったなら、
                # coefficients_by_t_degree[2] へ3を足す。
                t_degree = exponents[variable_kept_as_t_index]
                coefficients_by_t_degree[t_degree] += (
                    coefficient_after_substitution
                )

        # -----------------------------------------------------------------
        # 4. 係数を有限体F_pへ戻し、一変数多項式として返す
        # -----------------------------------------------------------------
        reduced_coefficients = [
            self.f.reduce(coefficient)
            for coefficient in coefficients_by_t_degree
        ]

        return UnivariatePolynomial(reduced_coefficients, self.p)

    def prove(self, challenges: list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values

        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        # 本物の対話型SumCheckでは、各g_iを証明者が送った「後」に、
        # 検証者がr_iをランダムに選ぶ。この教材では、その対話結果を
        # [(g_1, r_1), ..., (g_n, r_n)] としてまとめて返す。
        if challenges is not None and len(challenges) != self.n:
            raise ValueError("one challenge is required for each variable")

        # proofは、実際の対話を順番どおり記録したリスト。
        proof = []

        # ラウンドが進むたび、ここは
        #   [] -> [r_1] -> [r_1, r_2] -> ...
        # と増える。次のg_iを作るときに固定済み変数として使う。
        fixed_challenges = []

        for round_index in range(self.n):
            # -------------------------------------------------------------
            # 証明者の手番: g_i(t)を先に作る
            # -------------------------------------------------------------
            # g_i は「これまで」に受け取ったchallengeだけを使って作る。
            # 今回のr_iを先に渡さないことが、後出しを防ぐ順番に対応する。
            round_polynomial = self.construct_round_polynomial(
                fixed_challenges
            )

            # -------------------------------------------------------------
            # 検証者の手番: g_iを受け取った後でr_iを選ぶ
            # -------------------------------------------------------------
            if challenges is None:
                round_challenge = random.randrange(self.p)
            else:
                # challengeも有限体の要素として標準形 0 <= r_i < p にする。
                round_challenge = self.f.reduce(challenges[round_index])

            # 教材では通信の代わりに、今回の対話をproofへ記録する。
            round_transcript = (round_polynomial, round_challenge)
            proof.append(round_transcript)

            # 次のラウンドでは、今回の変数もr_iへ固定済みになる。
            fixed_challenges.append(round_challenge)

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
        # 変数がn個なら、主張を1変数ずつ減らすためにnラウンド必要。
        if len(proof) != self.n:
            return False

        # 最初に説明されるべき主張は、証明者が主張した全体の合計。
        # ラウンドが進むと、この変数は
        #   claimed_sum
        #     -> g_1(r_1)
        #       -> g_2(r_2)
        #         -> ...
        # と更新される。
        claim_to_be_explained = self.f.reduce(claimed_sum)
        verifier_challenges = []

        for round_index, (round_polynomial, verifier_challenge) in enumerate(proof):
            # -------------------------------------------------------------
            # 1. proofの構造と、低次数という約束を確認する
            # -------------------------------------------------------------
            if round_polynomial.p != self.p:
                return False

            if not 0 <= verifier_challenge < self.p:
                return False

            # 低次数であることが、ランダムな1点で嘘を見破れる根拠。
            # 元のfで変数iがd次なら、正直なg_iも高々d次になる。
            max_allowed_degree = max(
                exponents[round_index]
                for exponents in self.f.terms
            )
            if not round_polynomial.coefficients:
                return False

            # 末尾の0は次数を上げないため、リスト長ではなく、0でない係数を
            # 実際に持つ最大インデックスで次数を判断する。
            actual_degree = max(
                (
                    degree
                    for degree, coefficient
                    in enumerate(round_polynomial.coefficients)
                    if self.f.reduce(coefficient) != 0
                ),
                default=0,
            )
            if actual_degree > max_allowed_degree:
                return False

            # -------------------------------------------------------------
            # 2. 今回のg_iが、前の主張を説明しているか確認する
            # -------------------------------------------------------------
            # 各ラウンドの中心となる検査:
            #   説明されるべき前の主張 == g_i(0) + g_i(1)
            #
            # 第1ラウンドなら、これは
            #   claimed_sum == g_1(0) + g_1(1)
            # 第2ラウンド以降なら、
            #   g_{i-1}(r_{i-1}) == g_i(0) + g_i(1)
            claim_explained_by_round_polynomial = self.f.reduce(
                round_polynomial.evaluate(0)
                + round_polynomial.evaluate(1)
            )
            if claim_explained_by_round_polynomial != claim_to_be_explained:
                return False

            # -------------------------------------------------------------
            # 3. 抜き打ち点r_iで評価し、次のラウンドの主張へ縮小する
            # -------------------------------------------------------------
            # g_i(r_i)が、次のg_{i+1}で説明されるべき値になる。
            claim_to_be_explained = round_polynomial.evaluate(
                verifier_challenge
            )
            verifier_challenges.append(verifier_challenge)

        # -----------------------------------------------------------------
        # 4. 最後の主張を、元の多項式fへ接続する
        # -----------------------------------------------------------------
        # 最後の照合は、ラウンド間でつながってきた主張を元のfへ固定する。
        # これが無いと、互いに整合しているだけでfとは無関係な偽の
        # 多項式列を受理できてしまう。
        original_polynomial_value = self.f.evaluate(
            tuple(verifier_challenges)
        )
        return claim_to_be_explained == original_polynomial_value


# =========================================================== 簡易チェック

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

    for round_index, (round_polynomial, challenge) in enumerate(proof):
        print(
            f"Round {round_index + 1}:",
            f"g_{round_index + 1}(t) coefficients =",
            round_polynomial.coefficients,
            f", r_{round_index + 1} =",
            challenge,
        )

    print("Proof verified?:", sc.verify(claimed_sum, proof))
