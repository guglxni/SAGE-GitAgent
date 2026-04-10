#!/usr/bin/env bash
# post_tool_use.sh — Log tool results to session state
# Receives: JSON event on stdin with fields: tool_name, output, duration_ms
# Outputs: JSON response on stdout

set -euo pipefail

STATE_FILE=".gitagent/state.json"
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name','unknown'))" 2>/dev/null || echo "unknown")
DURATION=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('duration_ms', 0))" 2>/dev/null || echo "0")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -f "$STATE_FILE" ]; then
  python3 - <<PYEOF
import json

with open("$STATE_FILE", "r") as f:
    state = json.load(f)

# Update the last tool_call entry with duration
if state["tool_calls"] and state["tool_calls"][-1]["tool"] == "$TOOL_NAME":
    state["tool_calls"][-1]["duration_ms"] = $DURATION
    state["tool_calls"][-1]["completed_at"] = "$TIMESTAMP"

with open("$STATE_FILE", "w") as f:
    json.dump(state, f, indent=2)
PYEOF
fi

echo '{"status": "ok"}'
