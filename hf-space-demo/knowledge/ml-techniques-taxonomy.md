# ML Techniques Taxonomy

Reference taxonomy for SAGE's scan-codebase skill. Use this to map detected code patterns to canonical technique names and arXiv search terms.

## Attention and Transformers

| Detected Pattern | Canonical Name | arXiv Search Term |
|---|---|---|
| `nn.MultiheadAttention` | Multi-Head Self-Attention | "attention is all you need transformer" |
| `torch.nn.TransformerEncoder` | Standard Transformer Encoder | "BERT pre-training transformers" |
| `rotary` or `rope` in embeddings | Rotary Position Embedding (RoPE) | "RoFormer rotary position embedding" |
| `alibi` in attention bias | ALiBi Position Bias | "train short test long attention linear biases" |
| `flash_attn` import | Flash Attention | "flash attention fast memory-efficient exact attention" |
| grouped query attention | Grouped-Query Attention (GQA) | "grouped query attention GQA" |

## Optimizers

| Detected Pattern | Canonical Name | arXiv Search Term |
|---|---|---|
| `torch.optim.Adam` | Adam | "adam stochastic optimization" |
| `torch.optim.AdamW` | AdamW | "decoupled weight decay regularization AdamW" |
| `Lion` optimizer | Lion Optimizer | "symbolic discovery optimizers lion" |
| `Sophia` | Sophia Optimizer | "sophia scalable stochastic second-order optimizer" |
| `torch.optim.SGD` | SGD | "stochastic gradient descent" |
| `Muon` or `muon_optim` | Muon Optimizer | "muon orthogonal gradient descent" |

## Learning Rate Schedules

| Detected Pattern | Canonical Name | arXiv Search Term |
|---|---|---|
| `CosineAnnealingLR` | Cosine Annealing | "SGDR stochastic gradient descent warm restarts" |
| `warmup` in scheduler | Linear Warmup | "warmup learning rate transformer training" |
| `OneCycleLR` | One-Cycle Policy | "super-convergence one-cycle learning rate policy" |
| `get_linear_schedule_with_warmup` | Warmup + Linear Decay | "bert fine-tuning nlp warmup" |

## Regularization

| Detected Pattern | Canonical Name | arXiv Search Term |
|---|---|---|
| `nn.Dropout` | Dropout | "dropout simple way prevent overfitting" |
| `label_smoothing` in loss | Label Smoothing | "label smoothing rethinking inception" |
| `weight_decay` > 0 | Weight Decay (L2) | "decoupled weight decay AdamW" |
| `nn.LayerNorm` | Layer Normalization | "layer normalization" |
| `nn.RMSNorm` or `RMSNorm` | RMS Norm | "root mean square layer normalization RMSNorm" |

## Loss Functions

| Detected Pattern | Canonical Name | arXiv Search Term |
|---|---|---|
| `nn.CrossEntropyLoss` | Cross-Entropy Loss | "cross entropy loss classification" |
| `nn.BCEWithLogitsLoss` | Binary Cross-Entropy | "binary cross entropy sigmoid" |
| `InfoNCE` or `NT-Xent` | Contrastive Loss | "simple framework contrastive learning SimCLR" |
| `DPO` or `direct_preference` | DPO | "direct preference optimization DPO" |
| `nn.KLDivLoss` | KL Divergence | "knowledge distillation KL divergence" |

## Training Patterns

| Detected Pattern | Canonical Name | arXiv Search Term |
|---|---|---|
| `scaler.scale` / `GradScaler` | Mixed Precision (AMP) | "mixed precision training" |
| `gradient_accumulation_steps` | Gradient Accumulation | "gradient accumulation large batch training" |
| `clip_grad_norm_` | Gradient Clipping | "gradient clipping norm threshold" |
| `DistributedDataParallel` | DDP Distributed Training | "pytorch distributed data parallel" |
| `FullyShardedDataParallel` or `FSDP` | FSDP | "fully sharded data parallel FSDP" |
| `torch.compile` | torch.compile (Inductor) | "torch compile dynamo inductor" |

## Model Compression

| Detected Pattern | Canonical Name | arXiv Search Term |
|---|---|---|
| `LoraConfig` or `lora_` | LoRA | "lora low-rank adaptation large language models" |
| `bitsandbytes` or `load_in_4bit` | QLoRA / Quantization | "qlora efficient finetuning quantized llms" |
| `torch.quantization` | Post-Training Quantization | "quantization deep learning inference" |
| teacher-student `loss` pattern | Knowledge Distillation | "knowledge distillation neural network" |

## Architecture Patterns

| Detected Pattern | Canonical Name | arXiv Search Term |
|---|---|---|
| `UNet` or `down_blocks` + `up_blocks` | U-Net | "u-net convolutional networks biomedical" |
| `TimestepEmbedding` or `noise_pred` | Diffusion Model | "denoising diffusion probabilistic models DDPM" |
| `PatchEmbed` or `patch_size` | Vision Transformer (ViT) | "image worth 16x16 words vision transformer ViT" |
| `graph_conv` or `MessagePassing` | Graph Neural Network | "graph neural network semi-supervised classification" |

## Notable Absences (Patterns to Check For)

If these are NOT found in the codebase but the architecture would benefit from them, flag as a gap:

- No `clip_grad_norm_` with transformer training → likely Critical gap
- No `warmup` with Adam/AdamW → likely Improvement gap
- `Adam` instead of `AdamW` for transformer training → likely Improvement gap
- No `LayerNorm` or `RMSNorm` in transformer blocks → likely Critical gap
- No `GradScaler` for large model training on GPU → likely Improvement gap
