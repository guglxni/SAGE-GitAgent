#!/usr/bin/env bash
# on_session_start.sh — Initialize SAGE session state
# Receives: JSON event on stdin
# Outputs: JSON response on stdout

set -euo pipefail

SESSION_ID=$(date -u +"%Y%m%dT%H%M%SZ")
STATE_FILE=".gitagent/state.json"

mkdir -p .gitagent

# Initialize or reset session state
cat > "$STATE_FILE" <<EOF
{
  "session_id": "${SESSION_ID}",
  "agent": "sage-agent",
  "version": "2.0.0",
  "started_at": "${SESSION_ID}",
  "tool_calls": [],
  "sod_verifications": [],
  "errors": [],
  "pipeline_steps_completed": []
}
EOF

# Validate that Node.js and npx are available for gitnexus-query
if ! command -v npx &> /dev/null; then
  echo '{"warning": "npx not found — gitnexus-query tool will be unavailable"}' >&2
fi

echo '{"status": "ok", "message": "SAGE session initialized"}'
