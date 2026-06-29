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

cleanup() {
  rm -rf "$REPO_ROOT/frontend/dist"
}

trap cleanup EXIT

backend_status=0
frontend_status=0

printf '%s\n' 'Running backend smoke test...'
python3 scripts/smoke_backend.py || backend_status=$?

printf '%s\n' 'Running frontend smoke test...'
./scripts/smoke_frontend.sh || frontend_status=$?

cleanup

if [ "$backend_status" -eq 0 ] && [ "$frontend_status" -eq 0 ]; then
  printf '%s\n' 'PASS: all RailYatra checks completed successfully'
  exit 0
fi

printf 'FAIL: backend status=%s, frontend status=%s\n' \
  "$backend_status" "$frontend_status" >&2
exit 1
