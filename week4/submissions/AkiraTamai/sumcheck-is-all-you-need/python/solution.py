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
        # ex {(1,1): 1, (1,0): 1, (0,0): 2} -> (1,1), 1 ・・・
        for exp, coef in self.terms.items():
            term = coef
            for x, e in zip(point, exp):
                # term = term × x₁^e₁ × x₂^e₂ × ・・・
                # x^e mod pで既にmod pにより0...p-1で各べき乗の値は正規化済みだがterm *=結果やのちの+では未保証
                term *= pow(x, e, self.p)
            result += term
        # 有限体 F_p の正規化(ここで非負が保証される)
        return self.reduce(result)

class UnivariatePolynomial(Polynomial):
    """Class representing a univariate polynomial.

    terms: coefficients of a univariate polynomial
    p: order of finite field (a prime number)

    e.g.)
        [c_0, c_, ..., c_d] = c_0 + c_*x + ... + c_d*x^d
        例: [4, 3] は4+3x
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

        今回のケースでsum(c * x**i for i, c in enumerate(...))とすると、
        x^0, x^1, x^2... を個別に計算して乗算回数がO(d²)となるが、
        以下の方法だとO(d)になる
        (1つのべき乗だけならO(log e)、d次多項式全体の評価ならO(d)が下限)
        """
        result = 0
        # 前提のデータ構造として係数リストは低次から順に並ぶ
        # [c_0, c_, ..., c_d] = c_0 + c_*x + ... + c_d*x^d
        # 多項式は入れ子の形に書き換え可能 -> 内側から外側へ計算
        # c₀ + c₁x + c₂x² + c₃x³ = c₀ + x·(c₁ + x·(c₂ + x·c₃))
        for coef in reversed(self.coefficients):
            # ex. 2 + 3x + 5x²でxが4の場合
            # c₀ + c₁x + c₂x² = c₀ + x·(c₁ + x·c₂)
            # 2 + 3x + 5x² = 2 + x·(3 + x·5)
            # result = 0·4 + 5 = 5（c₂)
            # result = 5·4 + 3 = 23（c₂·x + c₁）
            # result = 23·4 + 2 = 94（c₂·x² + c₁·x + c₀)
            result = result * x + coef
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

    def construct_round_polynomial(self, challenges: list[int]) -> UnivariatePolynomial:
        """Constructs the round polynomial g_i(t) = Σf(r_1, ..., r_{i-1}, t, x_{i+1}, ..., x_n).
        　ラウンド多項式 g_i(t): ラウンドiで証明者が送る一変数多項式
          g_i(t) = Σf(r₁, ..., r{i-1}, t, x{i+1}, ..., x_n)

          test caseのf(x, y) = xy + x + 2、p=17、ラウンド1、challenges=[]
          ラウンド1の多項式：g₁(t) = Σ{y∈{0,1}} f(t, y) = f(t, 0) + f(t, 1)
          f(t, 0) = t*0 + t + 2 = t + 2
          f(t, 1) = t*1 + t + 2 = 2t + 2
          合計: g₁(t) = 3t + 4 → 係数リストを定数から記載[4, 3]

        Args:
            challenges: fixed random challenge values
        
        Returns:
            Univariate polynomial for a single round
        """
        # ラウンド1ならchallenges=[]でi=0
        i = len(challenges)

        # g_iのtに関する次数は全項の中での第i変数の最大指数
        degree = max(exponents[i] for exponents in self.f.terms)

        # その分の係数配列を0で用意
        coefficients = [0] * (degree + 1)

        # fの項ごとに、g_iへの寄与を計算
        # 各項は、「係数 × x₁^e₁ × ... × x_n^e_n」の形式と考えると、
        for exponents, coefficient in self.f.terms.items():
            term = coefficient
            # 固定変数をr_j^e_j
            for r, e in zip(challenges, exponents[:i]):
                term *= pow(r, e, self.p)
            # 変数ごとに独立に {0,1} の和を取れるので、
            # Σ_{x∈{0,1}} x^e = 0^e + 1^e = 2 if e == 0 else 1
            for e in exponents[i + 1:]:
                # e ≥ 1なら、0+1 = 1 -> 乗算しても変わらずno-op
                # e = 0なら、1+1 = 2
                if e == 0:
                    term *= 2
            # tは、term × t^(e_i)、f のその項の寄与
            # 次数e_iの係数スロットに加算するのは、fの複数の項が同じ次数のtに寄与(同類項まとめ)。
            # なお寄与しない場合はただの代入になる想定
            coefficients[exponents[i]] += term

        # 各係数をmod pして正規化。一変数多項式
        return UnivariatePolynomial(
            coefficients=[c % self.p for c in coefficients],
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

        # README: 全てのラウンド分の証明をまとめて生成するため、
        # Prover が g_i を送る → Verifier が r_i を返す → Prover が次の g_{i+1} を作る往復は行わない
        proof = []
        # nラウンド分ループ
        for i in range(self.n):
            # i=0、g₁(t) = Σf(t, x₂, ..., x_n) -> (g₁, r₁)を追加
            # i=1、g₂(t) = Σf(r₁, t, x₃, ..., x_n) -> (g₂, r₂)を追加
            # ...1変数ずつチャレンジ値で固定、操作毎に残りを一変数多項式に置き換え
            # n変数のfは変数が多くてそのままでは扱いにくいので、
            # 各ラウンドでn個の変数を役割ごとに処理してt以外を全部消す操作
            # なおチャレンジ値がg_iに依存せず事前に決まるのはREADME前提から(Verifierの乱数など不使用)
            g_i = self.construct_round_polynomial(challenges[:i])
            proof.append((g_i, challenges[i]))
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
        # README: 全てのラウンド分の証明をまとめて検証することが前提で以下
        # ラウンド数は変数の個数nと一致していなければ不正な証明
        if len(proof) != self.n:
            return False
        # 初期値は主張された総和のmod pで正規化後の値
        expected = self.f.reduce(claimed_sum)
        for g_i, r_i in proof:
            # g_i(0) + g_i(1)と期待値が一致するかどうかチェック
            # ラウンド1 -> g₁(0)+g₁(1) = expected
            # ラウンド2 -> g₂(0)+g₂(1) = g₁(r₁)
            # ・・・ -> g{i+1}(0)+g{i+1}(1) = g_i(r_i)
            if self.f.reduce(g_i.evaluate(0) + g_i.evaluate(1)) != expected:
                return False
            expected = g_i.evaluate(r_i)

        # expected = g_n(r_n)なので、全変数を (r₁, ..., r_n)に固定したfの値のclaim
        # そのためverifierはf自体を1点だけ直接評価して突き合わせ(検証者が実物のfに触れて検証するのはここから)
        #
        # ex. f = xy + x + 2、p=17、claimed_sum=11、challenges=[3,5]
        # proof -> [(g₁, r₁), (g₂, r₂)] -> [(g₁, 3), (g₂, 5)]
        #
        # prover側(construct_round_polynomial)により、
        # ラウンド1. g₁ = 4+3t: g₁(0)+g₁(1) = 4+7 = 11 → expected = g₁(3) = 13
        #.(g₁(t) = Σ_{y∈{0,1}} f(t, y) = f(t, 0) + f(t, 1) -> g₁(t) = 4+3t)
        #
        # ラウンド2. g₂ = 5+3t: g₂(0)+g₂(1) = 5+8 = 13 → expected = g₂(5) = 20 ≡ 3 (mod 17)
        # (g₂(t) = f(3, t) = 3t + 3 + 2 = 5 + 3t -> g₂(0) + g₂(1) はラウンと1のexpected 13と一致)
        # (next expected = g₂(5) = 5 + 3·5 = 20 ≡ 3 (mod 17))
        #
        # f(3, 5) の直接評価 ->  f(3, 5) = xy + x + 2 -> 15+3+2 = 20 ≡ 3 (mod 17) → True
        #
        # 仮にnが大きいときでも、証明のサイズとラウンド数はnに比例して増えない
        # 2^n個の点の総和の検証をせずとも、nペアの証明チェックとfの1点評価に置き換える操作(SumCheck)
        challenges = tuple(r for _, r in proof)
        return expected == self.f.evaluate(challenges)

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
