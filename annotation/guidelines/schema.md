# RegulQA Annotation – Minimal Guide

**Goal:** label ambiguity and regulation awareness for requirement sentences.

**Columns**
- id, source, tier, sector, document, req_text, ambig_presence, ambig_type, reg_clause, severity, notes

**Hints**
- *Lexical:* vague adjectives/adverbs (*quickly, user-friendly*), weak modals (*may, can*), open-ended quantifiers (*as needed, etc.*).
- *Syntactic:* pronoun ambiguity, nested clauses, unclear coordination/scope.
- *Semantic:* domain concept vagueness, missing units, missing pre/post-conditions.

**Severity**
- Low: Minor; still testable with assumptions
- Medium: Multiple plausible interpretations; testability impaired
- High: Not verifiable; safety/compliance risk

**Mapping**
- ISO/IEC/IEEE 29148 → clarity/unambiguity/verifiability
- ISO 26262 → precise/testable safety goals
- DO‑178C → unambiguous HLR/LLR for certification
- IEC 62304 → medical device SW lifecycle clarity
- NASA SWEHB → avoid weak/optional phrases
