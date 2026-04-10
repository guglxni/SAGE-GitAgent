# Scenario: SOD Verification Flow for Critical Gaps

## Context

SAGE has completed the `identify-gaps` skill and produced a draft with 3 Critical gaps. This scenario shows the expected paper-verifier handoff.

## Draft Input to paper-verifier

```json
{
  "gap": {
    "severity": "Critical",
    "description": "Missing Gradient Clipping",
    "arxiv_id": "2010.05522",
    "affected_file": "mingpt/trainer.py:L85-L92",
    "claim": "Paper shows gradient clipping is universally required for transformer training stability"
  },
  "techniques_context": "Transformer decoder-only model with Adam optimizer, no clip_grad_norm_ detected"
}
```

## Expected Approved Verdict

```json
{
  "verdict": "approved",
  "arxiv_id": "2010.05522",
  "reason": "fetch-abstract confirms paper exists and abstract discusses gradient norm thresholds in large-batch transformer training"
}
```

## Expected Rejected Verdict (hallucinated ID)

```json
{
  "verdict": "rejected",
  "arxiv_id": "2399.99999",
  "reason": "arxiv ID not found — fetch-abstract returned empty feed"
}
```

## Expected Flag Verdict (ambiguous claim)

```json
{
  "verdict": "flag-for-human-review",
  "arxiv_id": "2106.09685",
  "reason": "Paper exists but abstract discusses gradient clipping in RNN context, not transformers — claim extrapolation requires human judgment"
}
```

## Session State After Verification

```json
{
  "sod_verifications": [
    {"arxiv_id": "2010.05522", "verdict": "approved", "verifier": "paper-verifier"},
    {"arxiv_id": "2399.99999", "verdict": "rejected", "verifier": "paper-verifier"},
    {"arxiv_id": "2106.09685", "verdict": "flag-for-human-review", "verifier": "paper-verifier"}
  ]
}
```
