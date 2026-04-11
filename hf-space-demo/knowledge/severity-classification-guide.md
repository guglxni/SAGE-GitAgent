# Severity Classification Guide

Use this guide when running the `identify-gaps` skill to classify each detected gap consistently.

## Critical

Assign Critical when the gap:
- Causes training instability or divergence in known scenarios (e.g., missing gradient clipping with long-sequence transformers)
- Results in measurably worse model performance on standard benchmarks (verified by paper, not inferred)
- Represents a security or correctness issue (e.g., using deprecated loss function that introduces bias)
- Is universally adopted in the relevant architecture family (e.g., every modern transformer uses RMSNorm or LayerNorm — absence is a defect)

Examples:
- Missing `clip_grad_norm_` in a transformer training loop
- Using `Adam` without weight decay for LLM pre-training
- Missing causal mask in decoder-only model
- Using `nn.Softmax` + `nn.NLLLoss` instead of `nn.CrossEntropyLoss` (numerically unstable)

## Improvement

Assign Improvement when the gap:
- Would improve performance, training speed, or memory efficiency but is not causing active harm
- Is widely adopted but has a small migration cost (e.g., switching from Adam to AdamW)
- Represents a best practice that papers show consistent but non-dramatic benefit from
- Has a clear, low-to-medium complexity fix

Examples:
- Using cosine annealing without warmup (warmup is standard but not universally required)
- Not using `torch.compile` for a model that could benefit from it
- Using standard attention instead of Flash Attention (valid but slower)
- Missing mixed precision training (`GradScaler`)

## Experimental

Assign Experimental when the gap:
- Involves a technique that is promising but not yet universally validated
- Has conflicting evidence in the literature (some papers show benefit, others don't)
- Requires significant architectural changes to adopt
- Is domain-specific and may not apply to all use cases of the detected architecture
- Is a very recent technique (< 6 months old) without broad community adoption yet

Examples:
- Switching from AdamW to Lion or Sophia (promising but architecture-dependent)
- Adding speculative decoding to inference pipeline
- Applying DPO instead of RLHF for alignment
- Using Mamba or SSM layers instead of attention (novel architecture substitution)

## Decision Tree

```
Is the gap causing active harm (instability, wrong results, incorrect behavior)?
  YES → Critical

Is the gap universally adopted in this architecture family per multiple papers?
  YES → Critical

Would fixing it improve performance/efficiency AND is fix complexity Low-Medium?
  YES → Improvement

Is the evidence mixed, technique is recent, or fix requires major redesign?
  YES → Experimental
```

## Confidence Levels

Assign alongside severity:

- High: paper directly demonstrates the improvement on this architecture type, claim verified via fetch-abstract
- Medium: paper demonstrates improvement on a related architecture; extrapolation required
- Low: paper suggests potential benefit but evidence is limited or indirect
