# arXiv Category Codes for ML/AI Research

Use these category codes to narrow arXiv searches in the `hunt-papers` skill. Append `cat:cs.LG` to queries to filter for ML papers.

## Primary Categories

| Code | Full Name | Use When |
|---|---|---|
| cs.LG | Machine Learning | General ML techniques, training methods, optimizers |
| cs.AI | Artificial Intelligence | Agent systems, reasoning, planning |
| cs.CL | Computation and Language | NLP, LLMs, text generation, tokenization |
| cs.CV | Computer Vision and Pattern Recognition | Image models, CNNs, ViTs, diffusion models |
| cs.NE | Neural and Evolutionary Computing | Neural architecture search, evolutionary methods |
| stat.ML | Statistics — Machine Learning | Statistical learning theory, Bayesian methods |

## Secondary Categories

| Code | Full Name | Use When |
|---|---|---|
| cs.IR | Information Retrieval | RAG, embedding models, dense retrieval |
| cs.RO | Robotics | Reinforcement learning, embodied AI |
| eess.AS | Audio and Speech Processing | Speech models, audio transformers |
| q-bio.NC | Neurons and Cognition | Neuroscience-inspired architectures |

## Constructing Targeted Queries

For best results in `arxiv-search`, combine technique name with category:

```
"flash attention fast memory efficient" cat:cs.LG
"LoRA low-rank adaptation" cat:cs.CL
"diffusion model denoising" cat:cs.CV
"gradient clipping norm" cat:cs.LG
```

Prioritize `sortBy=relevance` and `sortOrder=descending`. Use `max_results=10` for broad technique searches, `max_results=5` for specific technique names.

## Date Filtering

arXiv papers from 2020 onwards are generally the most actionable for ML engineering. For optimizer and training technique searches, prefer 2022+ to capture recent improvements (Flash Attention 2, RoPE, ALiBi, Lion, GQA).
