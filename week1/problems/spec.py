"""spec.py — the public specification the circuit must enforce.

This is intentionally public: knowing WHAT "authorized" means is not the hard
part.  The hard part is writing constraints that let a proof exist *only* for
authorized credentials (soundness), and finding a witness that breaks a
deliberately under-constrained circuit (Part B).
"""

from __future__ import annotations

# Credential fields are integers in range 0..7 (think: role code, clearance
# level, region code).  A credential is AUTHORIZED iff every field is in its
# allowlist.  These allowlists are fixed and public.
CODE_MIN = 0
CODE_MAX = 7

ROLE_OK = (2, 5, 6)        # e.g. {ops, admin, root}
CLEARANCE_OK = (3, 4, 7)
REGION_OK = (1, 6)

FIELDS = ("role", "clearance", "region")
ALLOWLISTS = {"role": ROLE_OK, "clearance": CLEARANCE_OK, "region": REGION_OK}


def authorized(role: int, clearance: int, region: int) -> bool:
    """The reference predicate: granted must be 1 iff this is True."""
    return (
        role in ROLE_OK
        and clearance in CLEARANCE_OK
        and region in REGION_OK
    )


def all_credentials():
    """Enumerate the whole credential space (8*8*8 = 512)."""
    for role in range(CODE_MIN, CODE_MAX + 1):
        for clearance in range(CODE_MIN, CODE_MAX + 1):
            for region in range(CODE_MIN, CODE_MAX + 1):
                yield role, clearance, region
