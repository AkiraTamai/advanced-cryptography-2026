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

        Args:
            challenges: fixed random challenge values
        
        Returns:
            Univariate polynomial for a single round
        """
        raise NotImplementedError("Please implement this method.")

    def prove(self, challenges:list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values
        
        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        raise NotImplementedError("Please implement this method.")

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
        raise NotImplementedError("Please implement this method.")


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
