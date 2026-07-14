#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
OMNIGRAPH_CLUSTER="${OMNIGRAPH_CLUSTER:-/var/lib/omnigraph/cluster}"
OMNIGRAPH_TEMPLATE="${OMNIGRAPH_TEMPLATE:-/app/omnigraph}"
OMNIGRAPH_GRAPH_URI="${OMNIGRAPH_GRAPH_URI:-/var/lib/omnigraph/cluster/graphs/knowledge.omni}"
ANALYTOS_DB_PATH="${ANALYTOS_DB_PATH:-/var/lib/omnigraph/app/analytos_brain.db}"
INGEST_OUTPUT_DIR="${INGEST_OUTPUT_DIR:-/var/lib/omnigraph/app/ingestion}"
OMNIGRAPH_BIN="${OMNIGRAPH_BIN:-/usr/local/bin/omnigraph}"
OMNIGRAPH_SERVER_BIN="${OMNIGRAPH_SERVER_BIN:-/usr/local/bin/omnigraph-server}"
ANALYTOS_START_OMNIGRAPH_SERVER="${ANALYTOS_START_OMNIGRAPH_SERVER:-0}"
OMNIGRAPH_SERVER_BIND="${OMNIGRAPH_SERVER_BIND:-127.0.0.1:8080}"

export OMNIGRAPH_CLUSTER OMNIGRAPH_GRAPH_URI ANALYTOS_DB_PATH INGEST_OUTPUT_DIR OMNIGRAPH_BIN OMNIGRAPH_SERVER_BIN

SERVER_PID=""
API_PID=""

cleanup() {
  if [ -n "${API_PID}" ] && kill -0 "${API_PID}" >/dev/null 2>&1; then
    kill "${API_PID}" >/dev/null 2>&1 || true
  fi
  if [ -n "${SERVER_PID}" ] && kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup INT TERM EXIT

require_executable() {
  if [ ! -x "$1" ]; then
    echo "$2 executable is missing or not executable at $1." >&2
    exit 1
  fi
}

require_executable "${OMNIGRAPH_BIN}" "Omnigraph"
require_executable "${OMNIGRAPH_SERVER_BIN}" "Omnigraph server"

"${OMNIGRAPH_BIN}" version
"${OMNIGRAPH_SERVER_BIN}" --version

mkdir -p "${OMNIGRAPH_CLUSTER}" "$(dirname "${OMNIGRAPH_GRAPH_URI}")" "$(dirname "${ANALYTOS_DB_PATH}")" "${INGEST_OUTPUT_DIR}" /var/lib/omnigraph/policies

if [ ! -f "${OMNIGRAPH_CLUSTER}/cluster.yaml" ]; then
  cp -R "${OMNIGRAPH_TEMPLATE}/." "${OMNIGRAPH_CLUSTER}/"
fi

if [ ! -f "/var/lib/omnigraph/policies/analytos.cedar" ]; then
  cp -R /app/policies/. /var/lib/omnigraph/policies/
fi

if [ ! -e "${OMNIGRAPH_GRAPH_URI}" ]; then
  "${OMNIGRAPH_BIN}" init --schema "${OMNIGRAPH_CLUSTER}/schema.pg" "${OMNIGRAPH_GRAPH_URI}"
fi

"${OMNIGRAPH_BIN}" cluster validate --config "${OMNIGRAPH_CLUSTER}"
if [ ! -f "${OMNIGRAPH_CLUSTER}/__cluster/state.json" ]; then
  "${OMNIGRAPH_BIN}" cluster import --config "${OMNIGRAPH_CLUSTER}"
fi
"${OMNIGRAPH_BIN}" cluster plan --config "${OMNIGRAPH_CLUSTER}"
"${OMNIGRAPH_BIN}" cluster apply --config "${OMNIGRAPH_CLUSTER}"

if [ "${ANALYTOS_START_OMNIGRAPH_SERVER}" = "1" ]; then
  "${OMNIGRAPH_SERVER_BIN}" --cluster "${OMNIGRAPH_CLUSTER}" --bind "${OMNIGRAPH_SERVER_BIND}" &
  SERVER_PID="$!"
  sleep 2
  if ! kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    wait "${SERVER_PID}"
    exit 1
  fi
fi

python -m uvicorn apps.api.main:app --host 0.0.0.0 --port "${PORT}" &
API_PID="$!"
wait "${API_PID}"
