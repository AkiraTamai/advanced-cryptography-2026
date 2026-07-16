#!/usr/bin/env bash
# 提出フォルダを作成し、テンプレートをコピーする。
#
# 使い方:
#   bash scripts/new-submission.sh <week> <problem> [github-username]
#
# github-username を省略すると、gh または origin リモートから自動判定する。
# 例:
#   bash scripts/new-submission.sh week1 proof-of-exploit
set -euo pipefail

usage() {
  echo "Usage: bash scripts/new-submission.sh <week> <problem> [github-username]" >&2
}

fail() {
  echo "error: $*" >&2
  exit 1
}

require_safe_path_segment() {
  local name="$1" value="$2"
  [[ -n "$value" ]] || fail "$name must not be empty"
  [[ "$value" != "." && "$value" != ".." ]] || fail "$name must not be '.' or '..'"
  [[ "$value" != *"/"* ]] || fail "$name must not contain '/'"
}

detect_username() {
  local u=""
  if command -v gh >/dev/null 2>&1; then
    u="$(gh api user --jq .login 2>/dev/null || true)"
  fi
  if [[ -z "$u" ]]; then
    local url
    url="$(git remote get-url origin 2>/dev/null || true)"
    # git@github.com:owner/repo.git / https://github.com/owner/repo.git -> owner
    u="$(printf '%s' "$url" | sed -E 's#^(git@[^:]+:|https?://[^/]+/)##; s#/.*$##')"
  fi
  printf '%s' "$u"
}

if [[ "$#" -lt 2 || "$#" -gt 3 ]]; then
  usage
  exit 2
fi

WEEK="$1"
PROBLEM="$2"
USERNAME="${3:-}"

if [[ -z "$USERNAME" ]]; then
  USERNAME="$(detect_username)"
  [[ -n "$USERNAME" ]] || fail "could not detect github username; pass it as the 3rd argument"
fi

require_safe_path_segment "week" "$WEEK"
require_safe_path_segment "problem" "$PROBLEM"
require_safe_path_segment "github-username" "$USERNAME"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="$REPO_ROOT/$WEEK/problems/$PROBLEM/python/template"
DEST_DIR="$REPO_ROOT/$WEEK/submissions/$USERNAME/$PROBLEM/python"

[[ -d "$TEMPLATE_DIR" ]] || fail "no such problem template: $TEMPLATE_DIR"
[[ -e "$DEST_DIR/solution.py" ]] && fail "submission already exists: $DEST_DIR"

mkdir -p "$DEST_DIR"
cp "$TEMPLATE_DIR/solution.py" "$DEST_DIR/solution.py"
cp "$TEMPLATE_DIR/requirements.txt" "$DEST_DIR/requirements.txt"

REL="$WEEK/submissions/$USERNAME/$PROBLEM/python"
echo "created $REL  (github-username: $USERNAME)"
echo
echo "next:"
echo "  1. edit    $REL/solution.py"
echo "  2. test    bash scripts/test-python-submission.sh $WEEK $PROBLEM $USERNAME"
echo "  3. submit  bash scripts/submit.sh $WEEK $PROBLEM"
