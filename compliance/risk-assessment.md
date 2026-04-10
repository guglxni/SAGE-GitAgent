# Risk Assessment — SAGE Agent

## Risk Classification

**Risk Tier**: low

SAGE is a read-only research intelligence tool operating on local codebases with public API access (arXiv). It does not handle financial data, PII, or regulated content. It does not write to source code without explicit authorization.

## Capability Risk Map

| Capability | Risk | Mitigation |
|---|---|---|
| AST code scanning via gitnexus | Low — reads local files only | subprocess with no shell interpolation, pinned package version |
| arXiv API queries | Low — public read-only API | rate limiting (semaphore, max 50 results), no authentication tokens |
| Batch paper fetching | Low — public API, no auth | max 20 IDs, max 5 concurrent requests, 15s timeout |
| Writing output files | Low — only writes TECHNIQUES.md, PAPERS.md, SUMMARIES.md, GAPS.md, RELATED_WORK.md | no writes to source files unless explicitly requested |
| Sub-agent delegation to paper-verifier | Low — verifier has read-only tool access | verifier cannot write output files |

## Data Governance

- PII handling: not applicable (agent does not process PII)
- Data classification: all outputs are internal (non-public until user chooses to share)
- Source code privacy: source code content is never sent to any external API. Only file paths, technique names, and line numbers are used in prompts.
- Cross-border: not applicable

## Known Limitations

1. arXiv API availability: if arXiv is unreachable, paper-hunting and summarization steps fail gracefully but gap analysis cannot proceed. Partial runs are saved to state.
2. gitnexus version pinning: pinned to 0.22.2. If the package is removed from npm, the scan-codebase skill falls back to regex-based scanning with reduced accuracy.
3. LLM hallucination risk: the model may attempt to cite papers that do not exist. This is mitigated by the mandatory `fetch-abstract` verification step and the `paper-verifier` SOD handoff for Critical gaps.
4. Large repositories: repositories with more than 1000 files may cause gitnexus to timeout (120s limit). The agent logs a warning and proceeds with partial scan results.

## Residual Risk

Overall residual risk: **low**. SAGE operates in a sandboxed, read-only mode with multiple verification layers. The primary residual risk is LLM hallucination of paper citations, which is addressed by the verification requirements in RULES.md and the paper-verifier SOD architecture.
