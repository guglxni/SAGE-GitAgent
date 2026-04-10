---
name: identify-gaps
description: "Cross-references detected techniques against found papers to identify concrete implementation gaps, missing best practices, and opportunities"
license: MIT
metadata:
  author: aaryan-guglani
  version: "2.0.0"
  category: analysis
  risk_tier: low
  knowledge_refs: severity-classification-guide
---

# Identify Gaps

Compare the specific findings in `TECHNIQUES.md` to the state-of-the-art identified in `SUMMARIES.md` to flag concrete gaps between the codebase's current state and optimal literature implementations.

## Instructions

1. Read `TECHNIQUES.md` and `SUMMARIES.md` explicitly.
2. Consult `knowledge/severity-classification-guide.md` for classification rules and the decision tree.
3. For each paper in SUMMARIES.md, determine if the technique it introduces is: already present in the codebase, partially present but outdated, or entirely absent.
4. For techniques that are absent or outdated, write a gap entry.
5. Use the severity decision tree from the severity guide — do not guess severity.
6. Flag all Critical gaps for SOD verification by the `paper-verifier` sub-agent (they go to `GAPS-draft.md` first, not directly to `GAPS.md`).
7. Write a final summary statistics block at the top of the gaps output.

## Output Format (GAPS-draft.md / GAPS.md)

```markdown
# Gaps

## Summary

- Total gaps identified: N
- Critical: N | Improvement: N | Experimental: N
- Papers cited: N
- Verification status: [pending / complete]

---

### [Severity] [Gap Name/Description]
- **Paper**: [[arxiv ID]] [Paper Title]
- **Affected file**: `[file]:[line_range]`
- **Impact**: [Specific, measurable impact — not vague]
- **Fix complexity**: [Low / Medium / High]
- **Confidence**: [High / Medium / Low]
- **Verification**: [pending / approved / flagged] ← for Critical gaps only
```

## Output Format (RELATED_WORK.md)

Generate a valid LaTeX bibliography block citing all finalized papers used in the gap analysis. Use `@article` or `@misc` format. No markdown in this file.

```latex
@misc{arxivID,
  title={Paper Title},
  author={Author One and Author Two},
  year={YYYY},
  eprint={YYMM.NNNNN},
  archivePrefix={arXiv}
}
```
