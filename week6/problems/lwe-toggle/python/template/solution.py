from __future__ import annotations


def lwe_encrypt(bit: int, secret_key: list[int], a: list[int], e: int, modulus: int) -> int:
    """Return the LWE ciphertext component b for a 1-bit message.

    b = (dot(a, secret_key) + e + bit * (modulus // 2)) % modulus
    """
    raise NotImplementedError


def lwe_decrypt(a: list[int], b: int, secret_key: list[int], modulus: int) -> int:
    """Return the decrypted bit (0 or 1) for ciphertext (a, b).

    Use the circular distance mod `modulus` to decide whether
    (b - dot(a, secret_key)) mod modulus is closer to 0 or to modulus // 2.
    """
    raise NotImplementedError


def lwe_add(
    ct1: tuple[list[int], int],
    ct2: tuple[list[int], int],
    modulus: int,
) -> tuple[list[int], int]:
    """Return the component-wise sum of two ciphertexts modulo `modulus`."""
    raise NotImplementedError
