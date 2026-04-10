---
name: identify-gaps
description: "Cross-references detected techniques against found papers to identify concrete implementation gaps, missing best practices, and opportunities"
license: MIT
metadata:
  author: aaryan-guglani
  version: "1.0.0"
---

# Identify Gaps

Compare the specific findings in `TECHNIQUES.md` to the state-of-the-art identified in `SUMMARIES.md` to flag critical developmental disparities between the codebase's current state and optimal literature implementations.

## Instructions
1. Read both the `TECHNIQUES.md` and `SUMMARIES.md` files explicitly.
2. Identify missing best practices objectively (e.g., Code uses Adam, but literature strongly suggests AdamW for a specific task / architecture).
3. Classify each identified gap using the rigorous taxonomy: `🔴 Critical`, `🟡 Improvement`, `🟢 Experimental`.
4. Output these results exactly into `GAPS.md` and `RELATED_WORK.md` in the root of the project.

## Output Format (GAPS.md)
Format each entry as:
### [Severity Taxonomy] [Gap Name/Description]
- **Paper**: [[arxiv ID]] [Paper Title]
- **Affected file**: `[file]:[line_range]`
- **Impact**: [Why this matters specifically contextually]
- **Fix complexity**: [Low/Medium/High]
- **Confidence**: [High/Medium/Low]

## Output Format (RELATED_WORK.md)
Generate a simple LaTeX compatible bibliography block specifically citing all the finalized papers used.
