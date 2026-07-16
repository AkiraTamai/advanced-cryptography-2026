"""Week 1 — proof-of-exploit.  Copy this file to your submission and implement it:

    uv run python week1/problems/grade.py --new <your-github-username>
    # edit week1/submissions/<your-github-username>/solution.py
    uv run python week1/problems/grade.py <your-github-username>

You only write this one file.  Read week1/README.md and week1/problems/challenge.py
first.  The constraint DSL is week1/problems/aclib.py.

A "circuit" is a set of constraints over F_p that must all equal 0.  A signal is
*free* unless a constraint pins it down — that is the whole point of this task.
"""

from __future__ import annotations

from aclib import ConstraintSystem
from spec import ROLE_OK, CLEARANCE_OK, REGION_OK
import challenge


# ------------------------------------------------------------------ Part A
def build(cs: ConstraintSystem, role: int, clearance: int, region: int):
    """Build a SOUND & COMPLETE access-control circuit.

    granted == 1 must be satisfiable  if and only if
        role in ROLE_OK and clearance in CLEARANCE_OK and region in REGION_OK.

    Rules:
      * declare the three credential signals with the exact names
        "role", "clearance", "region" via cs.input(name, value).
      * declare helper signals with cs.aux(name, value).
      * add constraints with cs.assert_zero(expr).
      * declare the output with cs.set_output(granted).
      * the SET of signals/constraints must not depend on the input values,
        only on the public allowlists.

    Hint (membership flag): a boolean flag f with
        f * (x - a1) * (x - a2) * ... == 0   forces   f == 1  =>  x in {a1, a2, ...}.
    AND the three flags into `granted`.  Don't forget to make every flag a bit.
    """
    raise NotImplementedError


# ------------------------------------------------------------------ Part B
def attack() -> dict[str, int]:
    """Return a witness that BREAKS week1/problems/challenge.py.

    The dict maps every signal name in the challenge circuit to a field value.
    It must satisfy every challenge constraint, set granted == 1, and use an
    UNAUTHORIZED credential.

    Tip: start from challenge.honest_witness(role, clearance, region) for some
    authorized credential, then tamper with it to exploit the missing constraint.
    """
    raise NotImplementedError
