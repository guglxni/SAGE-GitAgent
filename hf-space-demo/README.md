---
title: SAGE Research Agent
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# SAGE — ML Research Intelligence Agent

Analyze any ML codebase against the latest arXiv papers. Drop a GitHub URL, choose your LLM provider (Groq/OpenAI/Anthropic/Custom), and SAGE runs a full research intelligence pipeline:

1. **scan-codebase** — AST analysis via gitnexus detects ML techniques, optimizers, architectures
2. **hunt-papers** — arXiv search for papers matching detected techniques
3. **identify-gaps** — gap analysis with paper citations and improvement recommendations

**Output:** `TECHNIQUES.md`, `PAPERS.md`, `GAPS.md` — downloadable reports

**Providers:** Groq (free), OpenAI, Anthropic, or any OpenAI-compatible endpoint (BYOK)

Source: [github.com/guglxni/SAGE-GitAgent](https://github.com/guglxni/SAGE-GitAgent)
