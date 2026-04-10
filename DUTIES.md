# Duties — Segregation of Duties Policy

## System Overview

SAGE operates a two-role pipeline: a **maker** (scanner + researcher) that produces findings, and a **checker** (verifier) that independently validates those findings before they appear in the final output. No single agent may hold both roles simultaneously.

## Roles

| Role | Agent | Permissions |
|------|-------|-------------|
| scanner | sage-agent | scan, query-ast, search-arxiv, fetch-abstracts, write-techniques, write-papers, write-summaries |
| researcher | sage-agent | search-arxiv, fetch-abstracts, write-papers, write-summaries |
| verifier | paper-verifier | fetch-abstracts, read-gaps-draft, approve, reject, flag |
| reporter | sage-agent | read-verified-gaps, write-gaps, write-related-work |

## Conflict Matrix

The following role pairs cannot be held by the same agent instance:

- `scanner` and `verifier` — the agent that extracts techniques cannot verify the gap claims derived from those techniques
- `researcher` and `verifier` — the agent that found the papers cannot be the one verifying them
- `reporter` and `verifier` — the agent writing the final report cannot be the one that approved its own content

## Handoff Workflows

### Critical Gap Verification (mandatory)

For any gap classified as Critical severity:

1. `sage-agent` (scanner + researcher roles) produces a draft gap entry.
2. `sage-agent` submits the draft to `paper-verifier` via sub-agent delegation.
3. `paper-verifier` (verifier role) independently fetches the cited paper and confirms: (a) the arxiv ID resolves to a real paper, (b) the paper actually supports the claimed technique improvement, (c) the affected file:line reference is plausible given the TECHNIQUES.md context.
4. `paper-verifier` returns `approved`, `rejected`, or `flag-for-human-review`.
5. Only `approved` entries proceed to `GAPS.md`. Rejected entries are dropped. Flagged entries are written to `GAPS-human-review.md` for human decision.

### Standard Gap Verification (advisory)

For Improvement and Experimental severity gaps:

1. `sage-agent` produces gap entries directly.
2. `paper-verifier` performs a spot-check (verify at least 1 in 3 non-critical entries).
3. Any rejection from the spot-check triggers full verification of all entries in that severity tier.

### Session Teardown

Before closing, `sage-agent` must confirm with `paper-verifier` that all Critical entries have been verified. If any are unverified at teardown, they are moved to `GAPS-pending.md` and excluded from `GAPS.md`.

## Isolation Policy

- State isolation: full — `paper-verifier` has no access to `sage-agent`'s intermediate working memory during a verification pass. It receives only the draft gap entry and TECHNIQUES.md context.
- Credential isolation: not applicable (no credentials required — public arXiv API only).

## Enforcement

Mode: **advisory** — violations are logged to `.gitagent/state.json` with a `sod_violation` key but do not block execution. This is set to advisory rather than strict because SAGE runs in environments without a full multi-process orchestrator. When running under gitclaw with sub-agent support, upgrade to strict.
