#!/bin/sh

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || {
  printf '%s\n' 'FAIL: could not locate the scripts directory' >&2
  exit 1
}

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd) || {
  printf '%s\n' 'FAIL: could not locate the repository root' >&2
  exit 1
}

cd "$REPO_ROOT" || {
  printf '%s\n' 'FAIL: could not enter the repository root' >&2
  exit 1
}

build_status=0
npm --prefix frontend run build || build_status=$?
rm -rf frontend/dist

if [ "$build_status" -eq 0 ]; then
  printf '%s\n' 'PASS: frontend production build completed'
  exit 0
fi

printf 'FAIL: frontend production build exited with status %s\n' "$build_status" >&2
exit "$build_status"
