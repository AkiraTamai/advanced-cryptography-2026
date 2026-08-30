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
        value = 0
        for term, coefficient in self.terms.items():
            if len(term) != len(point):
                raise ValueError("The number of variables in the term does not match the number of evaluation points.")
            term_value = coefficient
            for exponent, x in zip(term, point):
                term_value *= pow(x, exponent, self.p)
            term_value = self.reduce(term_value)
            value += term_value
            value = self.reduce(value)
        return self.reduce(value)

    def curry(self, fixed_values: dict[int, int]) -> 'Polynomial':
        """Curries the polynomial by fixing some variables.

        Args:
            fixed_values: fixed values for some variables (key: variable index, value: fixed value)
        
        Returns:
            A new polynomial with specified fixed variables
        """
        new_terms = {}
        assert all(i >= 0 and value < self.p for i, value in fixed_values.items()), "Fixed values must be less than p."
        for term, coefficient in self.terms.items():
            if len(term) < len(fixed_values):
                raise ValueError("The number of fixed values exceeds the number of variables in the polynomial.")
            new_term = tuple(exponent for i, exponent in enumerate(term) if i not in fixed_values)
            new_coefficient = coefficient
            for i, value in fixed_values.items():
                if i >= len(term) or i < 0:
                    raise ValueError("Fixed variable index exceeds the number of variables in the polynomial.")
                exponent = term[i]
                new_coefficient *= pow(value, exponent, self.p)
                new_coefficient = self.reduce(new_coefficient)
            if new_term in new_terms:
                new_terms[new_term] += new_coefficient
                new_terms[new_term] = self.reduce(new_terms[new_term])
            else:
                new_terms[new_term] = self.reduce(new_coefficient)
        return Polynomial(terms=new_terms, p=self.p)
    
    def __add__(self, other: 'Polynomial') -> 'Polynomial':
        """Adds two polynomials.

        Args:
            other: another polynomial
        
        Returns:
            A new polynomial representing the sum of the two polynomials
        """
        if self.p != other.p:
            raise ValueError("Polynomials must be over the same finite field.")
        ## Ignore case where the number of variables is different, as it is not relevant for this implementation.
        
        new_terms = self.terms.copy()
        for term, coefficient in other.terms.items():
            if term in new_terms:
                new_terms[term] += coefficient
                new_terms[term] = self.reduce(new_terms[term])
            else:
                new_terms[term] = self.reduce(coefficient)
        
        return Polynomial(terms=new_terms, p=self.p)

    def __radd__(self, other: 'int | Polynomial') -> 'Polynomial':
        """Adds two polynomials (right-hand side).

        Args:
            other: another polynomial
        
        Returns:
            A new polynomial representing the sum of the two polynomials
        """
        if other == 0:
            return  self
        if isinstance(other, Polynomial):
            return other + self
        raise ValueError("Unsupported type for addition. Must be an integer or a Polynomial.")
    
    def __neg__(self) -> 'Polynomial':
        """Negates the polynomial.

        Returns:
            A new polynomial representing the negation of the polynomial
        """
        new_terms = {term: self.reduce(-coefficient) for term, coefficient in self.terms.items()}
        return Polynomial(terms=new_terms, p=self.p)

    def __sub__(self, other: 'Polynomial') -> 'Polynomial':
        """Subtracts two polynomials.

        Args:
            other: another polynomial
        
        Returns:
            A new polynomial representing the difference of the two polynomials
        """
        return self.__add__(-other)
     
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
        terms = { (i,): coeff for i, coeff in enumerate(coefficients) if coeff != 0 }
        super().__init__(terms=terms, p=p)
        self.coefficients = coefficients

    def evaluate(self, x: int| tuple[int, ...]) -> int:
        """Evaluates polynomial at `x`.

        Args:
            x: evaluation point
        
        Returns:
            Evaluation result
        """
        if isinstance(x, int):
            return super().evaluate((x,))
        elif isinstance(x, list) or isinstance(x, tuple) and len(x) == 1:
            return super().evaluate(x)
        else:
            raise ValueError("Input must be an integer or a list containing a single integer.")
    
    def __add__(self, other: 'UnivariatePolynomial') -> 'UnivariatePolynomial':
        """Adds two univariate polynomials.

        Args:
            other: another univariate polynomial
        
        Returns:
            A new univariate polynomial representing the sum of the two polynomials
        """
        if self.p != other.p:
            raise ValueError("Polynomials must be over the same finite field.")
        
        new_coefficients = [0] * max(len(self.coefficients), len(other.coefficients))
        for i in range(len(new_coefficients)):
            coeff1 = self.coefficients[i] if i < len(self.coefficients) else 0
            coeff2 = other.coefficients[i] if i < len(other.coefficients) else 0
            new_coefficients[i] = self.reduce(coeff1 + coeff2)
        
        return UnivariatePolynomial(coefficients=new_coefficients, p=self.p)
    
    def __neg__(self) -> 'UnivariatePolynomial':
        """Negates the univariate polynomial.

        Returns:
            A new univariate polynomial representing the negation of the polynomial
        """
        new_coefficients = [self.reduce(-coeff) for coeff in self.coefficients]
        return UnivariatePolynomial(coefficients=new_coefficients, p=self.p)

def to_univariate_polynomial(poly: Polynomial) -> UnivariatePolynomial:
    """Converts a multivariate polynomial to a univariate polynomial.

    Args:
        poly: a multivariate polynomial
    
    Returns:
        A univariate polynomial
    """
    if len(next(iter(poly.terms))) != 1:
        raise ValueError("The input polynomial must be univariate.")
    
    coefficients = [0] * (max(term[0] for term in poly.terms) + 1)
    for term, coefficient in poly.terms.items():
        coefficients[term[0]] = coefficient
    
    return UnivariatePolynomial(coefficients=coefficients, p=poly.p)


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
            challenges: fixed random challenge values
        
        Returns:
            Univariate polynomial for a single round
        """
        front_curried_poly = self.f.curry(fixed_values={i: r for i, r in enumerate(challenges)})
        variable_index = len(challenges)
        challenge_poly: Polynomial = 0
        n_remaining_variables = self.n - variable_index

        for point in self.gen_boolean_points(n_remaining_variables - 1):
            fixed_point = {1+i: v for i, v in enumerate(point)}
            challenge_poly += front_curried_poly.curry(fixed_values=fixed_point)
        return to_univariate_polynomial(challenge_poly)

    def prove(self, challenges:list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values
        
        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        if challenges is None:
            challenges = [random.randint(0, self.p - 1) for _ in range(self.n)]
        proofs = []
        for i, challenge in enumerate(challenges):
            round_poly = self.construct_round_polynomial(challenges=challenges[:i])
            proofs.append((round_poly, challenge))
        return proofs

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
        expects = claimed_sum
        for round_poly, challenge in proof:
            if round_poly.reduce(round_poly.evaluate(0) + round_poly.evaluate(1)) != expects:
                return False
            expects = round_poly.reduce(round_poly.evaluate(challenge))
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
