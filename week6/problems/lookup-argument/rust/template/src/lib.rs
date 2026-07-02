use ark_bn254::Fr;
use ark_ff::One;

pub type F = Fr;

/// Return the product of all elements in `vals`.
/// Return F::one() when `vals` is empty.
pub fn grand_product(vals: &[F]) -> F {
    todo!()
}

/// Return the product of (challenge - v) for each v in `vals`.
/// Return F::one() when `vals` is empty.
pub fn fingerprint(vals: &[F], challenge: F) -> F {
    todo!()
}

/// Return true if `a` and `b` have the same length and the same
/// multiset of elements, checked via fingerprint equality at `challenge`.
pub fn is_permutation_check(a: &[F], b: &[F], challenge: F) -> bool {
    todo!()
}
