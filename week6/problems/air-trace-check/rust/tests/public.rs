use ark_bn254::Fr;

use submission::*;

fn f(x: u64) -> Fr {
    Fr::from(x)
}

fn neg(x: u64) -> Fr {
    -Fr::from(x)
}

#[test]
fn test_valid_execution_basic() {
    // init = 5
    // step0 Add(2): 5 + 2 = 7
    // step1 Mul(3): 7 * 3 = 21
    // step2 Add(-1): 21 - 1 = 20
    let program = vec![
        Instruction::Add(f(2)),
        Instruction::Mul(f(3)),
        Instruction::Add(neg(1)),
    ];
    let trace = vec![f(5), f(7), f(21), f(20)];

    assert!(check_transitions(&trace, &program));
    assert!(check_boundary(&trace, f(5), f(20)));
    assert!(is_valid_execution(&trace, &program, f(5), f(20)));
}

#[test]
fn test_add_only_program() {
    let program = vec![Instruction::Add(f(10)); 3];
    let trace = vec![f(1), f(11), f(21), f(31)];
    assert!(check_transitions(&trace, &program));
    assert!(is_valid_execution(&trace, &program, f(1), f(31)));
}

#[test]
fn test_mul_only_program() {
    let program = vec![Instruction::Mul(f(2)); 4];
    let trace = vec![f(1), f(2), f(4), f(8), f(16)];
    assert!(check_transitions(&trace, &program));
    assert!(is_valid_execution(&trace, &program, f(1), f(16)));
}

#[test]
fn test_single_row_no_instructions() {
    let program: Vec<Instruction> = vec![];
    let trace = vec![f(42)];
    assert!(check_transitions(&trace, &program));
    assert!(check_boundary(&trace, f(42), f(42)));
    assert!(is_valid_execution(&trace, &program, f(42), f(42)));
}

#[test]
fn test_empty_trace_is_invalid() {
    let program: Vec<Instruction> = vec![];
    let trace: Vec<Fr> = vec![];
    assert!(!check_transitions(&trace, &program));
    assert!(!check_boundary(&trace, f(0), f(0)));
    assert!(!is_valid_execution(&trace, &program, f(0), f(0)));
}

#[test]
fn test_transition_broken_in_middle() {
    let program = vec![Instruction::Add(f(2)), Instruction::Mul(f(3))];
    // Correct trace would be [5, 7, 21]; tamper the middle row.
    let trace = vec![f(5), f(8), f(21)];
    assert!(!check_transitions(&trace, &program));
    assert!(!is_valid_execution(&trace, &program, f(5), f(21)));
}

#[test]
fn test_boundary_wrong_init() {
    let program = vec![Instruction::Add(f(2)), Instruction::Mul(f(3))];
    let trace = vec![f(5), f(7), f(21)];
    assert!(check_transitions(&trace, &program));
    assert!(!check_boundary(&trace, f(999), f(21)));
    assert!(!is_valid_execution(&trace, &program, f(999), f(21)));
}

#[test]
fn test_boundary_wrong_output() {
    let program = vec![Instruction::Add(f(2)), Instruction::Mul(f(3))];
    let trace = vec![f(5), f(7), f(21)];
    assert!(check_transitions(&trace, &program));
    assert!(!check_boundary(&trace, f(5), f(999)));
    assert!(!is_valid_execution(&trace, &program, f(5), f(999)));
}

#[test]
fn test_trace_program_length_mismatch() {
    let program = vec![Instruction::Add(f(2)), Instruction::Mul(f(3))];
    // trace is missing the last row.
    let trace = vec![f(5), f(7)];
    assert!(!check_transitions(&trace, &program));

    let too_long_trace = vec![f(5), f(7), f(21), f(999)];
    assert!(!check_transitions(&too_long_trace, &program));
}
