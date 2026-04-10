# Teardown

Before ending the session, I complete the following in order:

1. Confirm that all pending SOD verifications have been resolved. Any unverified Critical gaps are moved to `GAPS-pending.md` rather than `GAPS.md`.
2. Write the final session summary to `.gitagent/state.json` via the `on_session_end` hook.
3. Report the pipeline completion summary: which output files were produced, how many gaps were identified per severity tier, and how many papers were verified.
4. If any errors occurred during the session, summarize them and suggest remediation steps.
5. Clean up any temporary `.draft` files created during the verification handoff.

I do not close the session until all Critical gap entries have a recorded verdict in `.gitagent/state.json`.
