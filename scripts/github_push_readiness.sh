#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
echo "RailYatra GitHub push readiness check"
echo "Mode: safe local Git/GitHub preparation"
rm -rf frontend/dist
rm -f docs/.PROJECT_STATUS.md.swp
BRANCH="$(git branch --show-current)"
echo "Current branch: $BRANCH"
if [ "$BRANCH" != "main" ]; then
  echo "FAIL: expected branch main"
  exit 1
fi
echo ""
echo "Git status:"
git status --short
if [ -n "$(git status --short)" ]; then
  echo "FAIL: working tree is not clean. Commit changes before pushing."
  exit 1
fi
echo ""
echo "Git remotes:"
git remote -v || true
if git remote get-url origin >/dev/null 2>&1; then
  ORIGIN_URL="$(git remote get-url origin)"
  echo ""
  echo "Origin remote found: $ORIGIN_URL"
  echo "Safe push command:"
  echo "git push -u origin main"
  echo "GITHUB PUSH READINESS RESULT: READY"
else
  echo ""
  echo "Origin remote not found."
  echo "Create an empty GitHub repo first, then run:"
  echo "git remote add origin YOUR_GITHUB_REPO_URL"
  echo "git push -u origin main"
  echo "GITHUB PUSH READINESS RESULT: NEEDS_REMOTE"
fi
