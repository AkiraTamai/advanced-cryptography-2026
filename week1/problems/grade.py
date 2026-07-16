#!/usr/bin/env python3
"""Week 1 helper — scaffold a submission and run the checks.  Pure standard
library, so `uv run` needs no dependencies.

Scaffold (creates week1/submissions/<username>/solution.py from the template):

    uv run python week1/problems/grade.py --new <username>

Test your submission:

    uv run python week1/problems/grade.py <username>
"""

from __future__ import annotations

import sys
from pathlib import Path

PROBLEMS_DIR = Path(__file__).resolve().parent          # week1/problems
WEEK_DIR = PROBLEMS_DIR.parent                          # week1
SUBMISSIONS_DIR = WEEK_DIR / "submissions"
TEMPLATE = PROBLEMS_DIR / "template.py"


def _usage() -> int:
    print((__doc__ or "").strip())
    return 2


def scaffold(username: str) -> int:
    dest_dir = SUBMISSIONS_DIR / username
    dest = dest_dir / "solution.py"
    if dest.exists():
        print(f"already exists: {dest.relative_to(WEEK_DIR.parent)} (edit it, or delete to reset)")
        return 1
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest.write_text(TEMPLATE.read_text())
    rel = dest.relative_to(WEEK_DIR.parent)
    print(f"created {rel}")
    print()
    print("next:")
    print(f"  1. edit   {rel}")
    print(f"  2. test   uv run python week1/problems/grade.py {username}")
    return 0


def grade(username: str) -> int:
    submission = SUBMISSIONS_DIR / username / "solution.py"
    if not submission.exists():
        print(f"no submission found: {submission.relative_to(WEEK_DIR.parent)}")
        print(f"create one with:  uv run python week1/problems/grade.py --new {username}")
        return 2

    # Make `import solution` (student) and the problem modules resolvable.
    sys.path.insert(0, str(submission.parent))
    sys.path.insert(0, str(PROBLEMS_DIR))
    import grader  # noqa: E402  (path set up above)
    import importlib

    solution = importlib.import_module("solution")
    print(f"grading week1 submission for {username!r}\n")
    ok = grader.run_all(solution)
    print()
    if ok:
        print("all checks passed ✓")
        return 0
    print("some checks failed ✗")
    return 1


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "--new":
        return scaffold(argv[1])
    if len(argv) == 1 and not argv[0].startswith("-"):
        return grade(argv[0])
    return _usage()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
