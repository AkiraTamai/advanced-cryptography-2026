from __future__ import annotations


def share(secret: int, randomness: list[int], modulus: int) -> list[int]:
    """Split `secret` into len(randomness) + 1 additive shares mod `modulus`.

    The last share is (secret - sum(randomness)) % modulus. Every returned
    share must be a canonical field element in [0, modulus).
    """
    raise NotImplementedError


def reconstruct(shares: list[int], modulus: int) -> int:
    """Return sum(shares) % modulus."""
    raise NotImplementedError


def add_shares(shares_a: list[int], shares_b: list[int], modulus: int) -> list[int]:
    """Return the component-wise sum of two share vectors mod `modulus`.

    This requires no communication between parties.
    """
    raise NotImplementedError


def scale_shares(shares: list[int], scalar: int, modulus: int) -> list[int]:
    """Return each share multiplied by the public `scalar`, mod `modulus`.

    This requires no communication between parties.
    """
    raise NotImplementedError


def beaver_multiply(
    x_shares: list[int],
    y_shares: list[int],
    a_shares: list[int],
    b_shares: list[int],
    c_shares: list[int],
    modulus: int,
) -> list[int]:
    """Return shares of x * y using a pre-shared Beaver triple (a, b, c).

    Assumes c = a * b (mod modulus) and that all inputs are additive
    shares of the same length. See the README for the protocol steps.
    """
    raise NotImplementedError
