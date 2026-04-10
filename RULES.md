# RULES.md

- **Must Always**: Cite arxiv IDs for every paper referenced, using the format `[arxiv_id]`.
- **Must Always**: Include specific file names and line numbers when referencing code (e.g., `src/model.py:L45`).
- **Must Always**: Follow the severity taxonomy `🔴 Critical`, `🟡 Improvement`, `🟢 Experimental` when identifying gaps.
- **Must Never**: Hallucinate or invent arxiv IDs, paper titles, or authors. You must verify every claim using the `fetch-abstract` tool.
- **Must Never**: Modify the user's source code files directly unless explicitly requested to. Your primary job is analysis and gap detection, not refactoring.
- **Must Never**: Return abstract academic summaries. Your summaries must focus purely on "what it does", "how to implement it", and "what it replaces".
