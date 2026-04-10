#!/usr/bin/env bash
# on_session_end.sh — Finalize session, verify SOD completion, summarize run
# Receives: JSON event on stdin
# Outputs: JSON response on stdout

set -euo pipefail

STATE_FILE=".gitagent/state.json"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -f "$STATE_FILE" ]; then
  python3 - <<PYEOF
import json, os

with open("$STATE_FILE", "r") as f:
    state = json.load(f)

state["ended_at"] = "$TIMESTAMP"
state["tool_call_count"] = len(state.get("tool_calls", []))
state["error_count"] = len(state.get("errors", []))
state["sod_verification_count"] = len(state.get("sod_verifications", []))

# Check which output files were produced
output_files = []
for fname in ["TECHNIQUES.md", "PAPERS.md", "SUMMARIES.md", "GAPS.md", "RELATED_WORK.md"]:
    if os.path.exists(fname):
        output_files.append(fname)
state["output_files_produced"] = output_files

with open("$STATE_FILE", "w") as f:
    json.dump(state, f, indent=2)

print(json.dumps({
    "status": "ok",
    "tool_calls": state["tool_call_count"],
    "errors": state["error_count"],
    "sod_verifications": state["sod_verification_count"],
    "output_files": output_files
}))
PYEOF
else
  echo '{"status": "ok", "message": "No state file found — session may not have been fully initialized"}'
fi
