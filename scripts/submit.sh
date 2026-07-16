#!/usr/bin/env bash
# 提出をテストし、合格したら branch を切って commit・push・PR 作成まで行う。
#
# 使い方:
#   bash scripts/submit.sh <week> <problem> [github-username]
#
# github-username を省略すると、gh または origin リモートから自動判定する。
set -euo pipefail

usage() {
  echo "Usage: bash scripts/submit.sh <week> <problem> [github-username]" >&2
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
SUBMISSION_REL="$WEEK/submissions/$USERNAME/$PROBLEM/python"
[[ -f "$REPO_ROOT/$SUBMISSION_REL/solution.py" ]] || \
  fail "no submission at $SUBMISSION_REL — run: bash scripts/new-submission.sh $WEEK $PROBLEM"

echo "==> running tests"
bash "$REPO_ROOT/scripts/test-python-submission.sh" "$WEEK" "$PROBLEM" "$USERNAME"
echo "==> tests passed"

BRANCH="submit/$WEEK-$USERNAME"
echo "==> preparing branch $BRANCH"
git -C "$REPO_ROOT" switch -c "$BRANCH" 2>/dev/null || git -C "$REPO_ROOT" switch "$BRANCH"
git -C "$REPO_ROOT" add "$WEEK/submissions/$USERNAME/"

if git -C "$REPO_ROOT" diff --cached --quiet; then
  echo "nothing to commit (submission already committed)"
else
  git -C "$REPO_ROOT" commit -m "submit $WEEK"
fi

echo "==> pushing to origin"
git -C "$REPO_ROOT" push -u origin "$BRANCH"

TITLE="[$WEEK] $USERNAME"
if command -v gh >/dev/null 2>&1; then
  echo "==> creating pull request"
  gh pr create \
    --repo zk-tokyo/advanced-cryptography-2026 \
    --base main \
    --head "$USERNAME:$BRANCH" \
    --title "$TITLE" \
    --body "Submission for $WEEK ($PROBLEM)." \
    || echo "could not create PR automatically; open it on GitHub with title: $TITLE"
else
  echo "gh not found. Open a PR on GitHub:"
  echo "  base: zk-tokyo/advanced-cryptography-2026  main"
  echo "  head: $USERNAME:$BRANCH"
  echo "  title: $TITLE"
fi
