use ark_bn254::Fr;
use ark_ff::One;

use submission::*;

fn f(x: u64) -> Fr {
    Fr::from(x)
}

#[test]
fn test_grand_product_basic() {
    assert_eq!(grand_product(&[f(2), f(3), f(4)]), f(24));
}

#[test]
fn test_grand_product_empty() {
    assert_eq!(grand_product(&[]), Fr::one());
}

#[test]
fn test_grand_product_single() {
    assert_eq!(grand_product(&[f(7)]), f(7));
}

#[test]
fn test_fingerprint_basic() {
    let vals = vec![f(1), f(2), f(3)];
    assert_eq!(fingerprint(&vals, f(10)), f(504));
}

#[test]
fn test_fingerprint_empty() {
    assert_eq!(fingerprint(&[], f(10)), Fr::one());
}

#[test]
fn test_fingerprint_zero_at_matching_root() {
    let vals = vec![f(5), f(6), f(7)];
    assert_eq!(fingerprint(&vals, f(5)), Fr::from(0u64));
}

#[test]
fn test_is_permutation_check_true_reordered() {
    let a = vec![f(1), f(2), f(3)];
    let b = vec![f(3), f(1), f(2)];
    assert!(is_permutation_check(&a, &b, f(999)));
    assert!(is_permutation_check(&a, &b, f(12345)));
}

#[test]
fn test_is_permutation_check_true_empty() {
    assert!(is_permutation_check(&[], &[], f(42)));
}

#[test]
fn test_is_permutation_check_false_different_length() {
    let a = vec![f(1), f(2)];
    let b = vec![f(1), f(2), f(3)];
    assert!(!is_permutation_check(&a, &b, f(999)));
}

#[test]
fn test_is_permutation_check_false_length_mismatch_with_coincidental_fingerprint() {
    // fingerprint([], 100) = 1, and fingerprint([99], 100) = 100 - 99 = 1.
    // The fingerprints collide even though the lengths differ, so a correct
    // implementation must check the length explicitly and not rely on the
    // fingerprint comparison alone.
    let a: Vec<Fr> = vec![];
    let b = vec![f(99)];
    assert!(!is_permutation_check(&a, &b, f(100)));
}

#[test]
fn test_is_permutation_check_false_different_multiplicity() {
    let a = vec![f(1), f(1), f(2)];
    let b = vec![f(1), f(2), f(2)];
    assert!(!is_permutation_check(&a, &b, f(999)));
    assert!(!is_permutation_check(&a, &b, f(54321)));
}

#[test]
fn test_is_permutation_check_false_different_values_same_sum() {
    let a = vec![f(1), f(4)];
    let b = vec![f(2), f(3)];
    assert!(!is_permutation_check(&a, &b, f(777)));
}
