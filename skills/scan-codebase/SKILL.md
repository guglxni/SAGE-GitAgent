---
name: scan-codebase
description: "Analyzes all source files in the repository to extract ML techniques, model architectures, training patterns, loss functions, and notable absences using AST knowledge graphs"
license: MIT
allowed-tools: gitnexus-query
metadata:
  author: aaryan-guglani
  version: "2.0.0"
  category: analysis
  risk_tier: low
  knowledge_refs: ml-techniques-taxonomy,arxiv-categories
---

# Scan Codebase

Analyze the current workspace codebase. Focus exclusively on Machine Learning, NLP, Computer Vision, and Deep Learning components.

## Instructions

1. Consult `knowledge/ml-techniques-taxonomy.md` to understand the canonical technique names and what code patterns map to them.
2. Use the `gitnexus-query` tool to search the knowledge graph AST. Run separate queries for each major category:
   - "classes extending torch.nn.Module"
   - "optimizer instantiations"
   - "loss function logic"
   - "learning rate scheduler usage"
   - "gradient clipping clip_grad_norm_"
   - "mixed precision GradScaler"
   - "distributed training DistributedDataParallel FSDP"
3. Focus on resolving explicit model definitions and training parameters structurally, not through raw text.
4. Identify architectural paradigms (Transformers, CNNs, GANs, Diffusion), training patterns (distributed training, gradient accumulation, mixed precision), and specific algorithms used or obviously missing.
5. Cross-check the detected patterns against the "Notable Absences" section of `knowledge/ml-techniques-taxonomy.md`. Flag any standard patterns that are absent for the detected architecture type.
6. Output findings as `TECHNIQUES.md` in the root of the project.

## Output Format (TECHNIQUES.md)

```markdown
# Techniques

## Detected Techniques

- **[Technique Name]** — `[file_path]:[line_range]`
  - Brief description of how it is used.
  - Hyperparameter notes (if applicable).

## Notable Absences

- **[Missing Technique]** — expected for [detected architecture type]
  - Why this is expected and what risk the absence creates.
```
