use ark_bn254::Fr;

pub type F = Fr;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Instruction {
    Add(F),
    Mul(F),
}

fn step(state: F, instr: &Instruction) -> F {
    match instr {
        Instruction::Add(k) => state + k,
        Instruction::Mul(k) => state * k,
    }
}

/// Return true iff trace.len() == program.len() + 1 and, for every i,
/// trace[i + 1] equals `step(trace[i], &program[i])`.
pub fn check_transitions(trace: &[F], program: &[Instruction]) -> bool {
    todo!()
}

/// Return true iff `trace` is non-empty, trace[0] == init, and the last
/// element of `trace` equals `expected_output`.
pub fn check_boundary(trace: &[F], init: F, expected_output: F) -> bool {
    todo!()
}

/// Return true iff both check_transitions and check_boundary hold.
pub fn is_valid_execution(
    trace: &[F],
    program: &[Instruction],
    init: F,
    expected_output: F,
) -> bool {
    todo!()
}
