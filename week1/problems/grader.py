"""grader.py — the checks your submission must pass.

Nothing here is hidden: the checks are exactly the properties your circuit and
your exploit must have.  Passing them means you actually understood soundness,
not that you matched a fixed answer.

You don't run this directly — use:  uv run python week1/problems/grade.py <username>
"""

from __future__ import annotations

from aclib import ConstraintSystem
from spec import authorized, all_credentials
import challenge
import solver


class CheckFailure(AssertionError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def _build(solution, role, clearance, region) -> ConstraintSystem:
    cs = ConstraintSystem()
    solution.build(cs, role, clearance, region)
    return cs


def _structure(cs: ConstraintSystem):
    return tuple(cs.idx2name), tuple(
        tuple(sorted(expr.terms.items())) for expr in cs.constraints
    )


# --------------------------------------------------------------- Part A
def check_interface(solution) -> None:
    _require(callable(getattr(solution, "build", None)), "solution.py must define build()")
    _require(callable(getattr(solution, "attack", None)), "solution.py must define attack()")
    cs = _build(solution, 2, 3, 1)
    for field in ("role", "clearance", "region"):
        _require(
            field in cs.name2idx,
            f"declare the credential signal {field!r} with cs.input({field!r}, ...)",
        )
    _require(cs.output_idx is not None, "call cs.set_output(granted) to declare the output")


def check_completeness(solution) -> None:
    for role, clearance, region in all_credentials():
        if not authorized(role, clearance, region):
            continue
        cs = _build(solution, role, clearance, region)
        assignment = {name: cs.values[idx] for name, idx in cs.name2idx.items()}
        bad = cs.first_unsatisfied(assignment)
        _require(
            bad is None,
            f"authorized credential {(role, clearance, region)} does not satisfy your "
            f"own constraint #{bad}",
        )
        _require(
            cs.values[cs.output_idx] == 1,
            f"granted must be 1 for authorized credential {(role, clearance, region)}",
        )


def check_structure(solution) -> None:
    a = _structure(_build(solution, 2, 3, 1))
    b = _structure(_build(solution, 5, 4, 6))
    _require(
        a == b,
        "your circuit structure changes with the input values; the set of signals "
        "and constraints must be the same for every credential.",
    )


def check_soundness(solution) -> None:
    cs = _build(solution, 2, 3, 1)
    exploit = solver.find_exploit(cs.constraints, cs.name2idx, cs.output_idx)
    if exploit is not None:
        cred, assignment = exploit
        raise CheckFailure(
            "your circuit is under-constrained: the unauthorized credential "
            f"role/clearance/region={cred} can still reach granted=1. witness found "
            f"by the grader: {assignment}. Add constraints that force each flag to "
            "imply membership."
        )


# --------------------------------------------------------------- Part B
def check_exploit(solution) -> None:
    cs = ConstraintSystem()
    challenge.build(cs, 0, 0, 0)  # placeholder inputs; we grade your assignment
    witness = solution.attack()
    _require(isinstance(witness, dict), "attack() must return a dict signal->int")
    missing = [n for n in cs.name2idx if n not in witness]
    _require(not missing, f"attack() witness is missing signals: {missing}")
    bad = cs.first_unsatisfied(witness)
    _require(
        bad is None,
        f"your witness does not satisfy challenge constraint #{bad}; it must pass "
        "every constraint in challenge.py",
    )
    _require(witness["granted"] == 1, "your exploit must set granted == 1")
    role, clearance, region = (witness["role"] % 8, witness["clearance"] % 8, witness["region"] % 8)
    _require(
        not authorized(role, clearance, region),
        f"the credential {(role, clearance, region)} is actually authorized; an exploit "
        "must use an UNAUTHORIZED credential",
    )


CHECKS = [
    ("Part A · interface", check_interface),
    ("Part A · completeness", check_completeness),
    ("Part A · structure", check_structure),
    ("Part A · soundness", check_soundness),
    ("Part B · exploit", check_exploit),
]


def run_all(solution) -> bool:
    """Run every check; print a report; return True iff all passed."""
    ok = True
    for name, check in CHECKS:
        try:
            check(solution)
            print(f"  PASS  {name}")
        except CheckFailure as exc:
            ok = False
            print(f"  FAIL  {name}\n        {exc}")
        except Exception as exc:  # noqa: BLE001 - surface any crash as a failure
            ok = False
            print(f"  ERROR {name}\n        {type(exc).__name__}: {exc}")
    return ok
