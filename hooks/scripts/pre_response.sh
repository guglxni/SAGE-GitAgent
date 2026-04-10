#!/usr/bin/env bash
# pre_response.sh — Validate output files before finalizing a pipeline step
# Receives: JSON event on stdin with fields: response_type, output_files
# Outputs: JSON response on stdout (block: true to prevent write)

set -euo pipefail

INPUT=$(cat)

# Check if we're about to write GAPS.md — require SOD verification
RESPONSE_TYPE=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('response_type',''))" 2>/dev/null || echo "")

if [[ "$RESPONSE_TYPE" == "write_gaps" ]]; then
  STATE_FILE=".gitagent/state.json"
  if [ -f "$STATE_FILE" ]; then
    SOD_COUNT=$(python3 -c "
import json
with open('$STATE_FILE') as f:
    state = json.load(f)
print(len(state.get('sod_verifications', [])))
" 2>/dev/null || echo "0")

    if [ "$SOD_COUNT" -eq "0" ]; then
      echo '{"block": false, "warning": "No SOD verifications recorded — paper-verifier was not invoked. Advisory mode: proceeding."}'
      exit 0
    fi
  fi
fi

echo '{"block": false}'
