#!/usr/bin/env bash
# pre_tool_use.sh — Log and gate tool invocations
# Receives: JSON event on stdin with fields: tool_name, input
# Outputs: JSON response on stdout

set -euo pipefail

STATE_FILE=".gitagent/state.json"
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name','unknown'))" 2>/dev/null || echo "unknown")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log tool invocation to state
if [ -f "$STATE_FILE" ]; then
  python3 - <<PYEOF
import json, sys

with open("$STATE_FILE", "r") as f:
    state = json.load(f)

state["tool_calls"].append({
    "tool": "$TOOL_NAME",
    "timestamp": "$TIMESTAMP",
    "phase": "pre"
})

with open("$STATE_FILE", "w") as f:
    json.dump(state, f, indent=2)
PYEOF
fi

# Block any tool not in the approved list
APPROVED_TOOLS="arxiv-search fetch-abstract gitnexus-query"
if [[ ! " $APPROVED_TOOLS " =~ " $TOOL_NAME " ]]; then
  echo "{\"block\": true, \"reason\": \"Tool '$TOOL_NAME' is not in the approved tool list for sage-agent\"}"
  exit 0
fi

echo '{"block": false}'
