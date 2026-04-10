#!/usr/bin/env bash
# on_error.sh — Log errors to session state
# Receives: JSON event on stdin with fields: error_type, message, tool_name
# Outputs: JSON response on stdout

set -euo pipefail

STATE_FILE=".gitagent/state.json"
INPUT=$(cat)

ERROR_TYPE=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('error_type','unknown'))" 2>/dev/null || echo "unknown")
MESSAGE=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('message',''))" 2>/dev/null || echo "")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -f "$STATE_FILE" ]; then
  python3 - <<PYEOF
import json

with open("$STATE_FILE", "r") as f:
    state = json.load(f)

state["errors"].append({
    "type": "$ERROR_TYPE",
    "message": "$MESSAGE",
    "timestamp": "$TIMESTAMP"
})

with open("$STATE_FILE", "w") as f:
    json.dump(state, f, indent=2)
PYEOF
fi

echo '{"status": "logged"}'
