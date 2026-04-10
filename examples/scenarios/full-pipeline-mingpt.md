# Scenario: Full Pipeline on minGPT

## Context

Target repository: `karpathy/minGPT` — a minimal PyTorch GPT implementation.

## Expected Scan Output (TECHNIQUES.md)

```markdown
# Techniques

## Detected Techniques

- **Transformer (decoder-only)** — `mingpt/model.py:L45-L120`
  - Uses nn.MultiheadAttention with n_head heads (configurable, default 8).
  - Causal mask applied via register_buffer in CausalSelfAttention.
  - Hidden dimension: n_embd (default 768). Dropout: 0.1.

- **GELU Activation** — `mingpt/model.py:L89`
  - Uses torch.nn.functional.gelu as non-linearity in MLP blocks.

- **Adam Optimizer** — `mingpt/trainer.py:L67`
  - torch.optim.AdamW with weight_decay=0.1, betas=(0.9, 0.95).
  - Learning rate: 3e-4 (fixed, no scheduler).

- **Cross-Entropy Loss** — `mingpt/trainer.py:L89`
  - Standard nn.CrossEntropyLoss with default settings.

## Notable Absences

- **Gradient Clipping** — expected for transformer training with Adam
  - No clip_grad_norm_ call found in trainer.py. Risk: training instability on long sequences.

- **Learning Rate Warmup** — expected for transformer pre-training
  - No warmup schedule detected. Risk: unstable early training.

- **Mixed Precision (AMP)** — expected for GPU training efficiency
  - No GradScaler or autocast usage. Risk: slower training, higher memory usage.
```

## Expected Gap Output (excerpt from GAPS.md)

```markdown
### Critical — Missing Gradient Clipping
- **Paper**: [2010.05522] An Empirical Model of Large-Batch Training
- **Affected file**: `mingpt/trainer.py:L85-L92`
- **Impact**: Without clip_grad_norm_, gradient explosions occur in long-sequence autoregressive training. Standard practice since GPT-2.
- **Fix complexity**: Low (2 lines before optimizer.step())
- **Confidence**: High
- **Verification**: approved

### Improvement — No Learning Rate Warmup
- **Paper**: [1706.03762] Attention Is All You Need
- **Affected file**: `mingpt/trainer.py:L67`
- **Impact**: Warmup prevents large initial parameter updates that can destabilize transformer training. Improves final perplexity by ~0.5-1.0 on small datasets.
- **Fix complexity**: Low (add CosineAnnealingWarmRestarts or linear warmup)
- **Confidence**: High
```
