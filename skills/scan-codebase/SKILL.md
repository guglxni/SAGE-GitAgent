---
name: scan-codebase
description: "Analyzes all source files in the repository to extract ML techniques, model architectures, training patterns, loss functions, and notable absences using AST knowledge graphs"
license: MIT
allowed-tools: gitnexus-query
metadata:
  author: aaryan-guglani
  version: "1.0.0"
---

# Scan Codebase

Analyze the current workspace codebase. Focus exclusively on Machine Learning, NLP, Computer Vision, and Deep Learning components.

## Instructions
1. Utilize the `gitnexus-query` tool to search the knowledge graph AST. Example queries: "classes extending torch.nn.Module", "optimizer instantiations", "loss function logic".
2. Focus on resolving the explicit model definitions and training parameters structurally, not just through raw text.
3. Identify the architectural paradigms (e.g., Transformers, CNNs, GANs), training patterns (e.g., distributed training, gradient accumulation), and specific algorithms algorithms used (or obviously missing).
4. Output your findings precisely as a markdown file `TECHNIQUES.md` placed directly in the root of the project.

## Output Format (TECHNIQUES.md)
Format each detected technique exactly as follows:
- **[Technique Name]** — `[file_path]:[line_range]`
  - Brief description of how it is used.
  - Any hyperparameter notes.
