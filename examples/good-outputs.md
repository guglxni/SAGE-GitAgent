# Good Output Calibration Examples

Use the following as baseline examples of extremely high quality execution of your skills.

## Example: TECHNIQUES.md entry (High Quality)
- **Transformer (decoder-only)** — `src/model.py:L12-L45`
  - Uses standard `nn.MultiheadAttention` with 8 heads.
  - Causal mask applied in `src/model.py:L38`.
  - Hidden dimension of 512, dropout rate of 0.1 explicitly set.

## Example: GAPS.md entry (High Quality)
### 🔴 Missing Gradient Clipping
- **Paper**: [2310.01848] Gradient Clipping Revisited
- **Affected file**: `scripts/train.py:L78-L95`
- **Impact**: Without explicit `torch.nn.utils.clip_grad_norm_`, training instability will occur on long sequences.
- **Fix complexity**: Low (2 lines of code injected right before `optimizer.step()`)
- **Confidence**: High — this is universally standard practice.
