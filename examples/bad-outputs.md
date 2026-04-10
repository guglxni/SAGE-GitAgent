# Bad Output Calibration Examples

Use the following to understand exactly what to avoid during output generation. DO NOT execute outputs that resemble these anti-patterns:

## Bad: Hallucinated/Invented Paper ID
❌ "Paper [2399.99999] describes a novel approach..."
→ **Why bad**: This arxiv ID does not exist in the database. NEVER cite a paper without verifying it directly via `fetch-abstract`.

## Bad: Vague gap with no direct code reference
❌ "The codebase could benefit from better optimization."
→ **Why bad**: Missing vital specifications: which file, which exact line, what specific technique, and which paper explicitly supports this adjustment.

## Bad: Missing strict severity classification
❌ "Consider adding gradient accumulation."
→ **Why bad**: Must use the exact defined `🔴/🟡/🟢` taxonomy mapping. You must specify whether this is critical, a minor improvement, or purely experimental.
