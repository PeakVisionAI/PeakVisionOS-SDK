#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PVOS_BIN="${PVOS_BIN:-${PYTHON_BIN} -m pvos.cli}"

cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/python${PYTHONPATH:+:${PYTHONPATH}}"

echo "[release-gate] Python contract tests"
for test_file in \
  tests/test-local-client.py \
  tests/test-sdk-http.py \
  tests/test-pvos-toolchain.py \
  tests/test-harness.py; do
  "${PYTHON_BIN}" "${test_file}"
done

echo "[release-gate] Python compilation"
"${PYTHON_BIN}" -m compileall -q python

echo "[release-gate] package build"
"${PYTHON_BIN}" -m build python

if [[ -n "${PVOS_GATEWAY_ENDPOINT:-}" ]]; then
  agent="${PVOS_AGENT:-demo-agent}"
  timeout="${PVOS_TIMEOUT:-30}"
  echo "[release-gate] live Gateway acceptance (${agent})"
  # shellcheck disable=SC2086
  ${PVOS_BIN} acceptance \
    --endpoint "${PVOS_GATEWAY_ENDPOINT}" \
    --token "${PVOS_TOKEN:-}" \
    --agent "${agent}" \
    --timeout "${timeout}"
else
  echo "[release-gate] live Gateway acceptance skipped"
  echo "[release-gate] set PVOS_GATEWAY_ENDPOINT to run it"
fi

echo "[release-gate] PASS"
