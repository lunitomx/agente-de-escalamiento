# ESCALA-001: retrospective

## Summary

- Root cause: commit `c9b119d` changed the canonical terminal-disposition
  vocabulary without changing the validator's exact-string contract or tests.
- Fix approach: retain the truthful terminal dispositions and synchronize each
  exact per-epic rule with fail-closed regression coverage.
- Classification: Regression / S1-High / Integration / Incorrect.
- Review verdict: the implementation addresses the confirmed root cause; no
  permissive aliases or manufactured completion evidence were introduced.

## Process Improvement

**Prevention:** Treat governed status vocabulary as a versioned contract. A
change to a canonical `Status` or evidence heading must update the artifact,
validator rule, and positive/negative contract tests in the same commit. E36
should move this vocabulary to one typed source of truth so Markdown and
validation cannot evolve independently.

**Pattern:** Regression + Integration + Incorrect means two individually
reasonable layers changed out of sequence: the documentation acquired a more
truthful terminal taxonomy while the executable consumer remained on the old
taxonomy.

## Heutagogical Checkpoint

1. **Learned:** these governance Markdown files are executable inputs, not only
   documentation. A semantically safer label can still be a breaking contract
   change when a validator compares exact normalized strings.
2. **Process change:** run closure-governance tests in the same change that
   touches canonical status headings, and review the diff as one contract
   migration rather than a documentation-only edit.
3. **Framework improvement:** bugfix guidance should explicitly support a RED
   checkpoint without a RED commit when repository policy requires every commit
   to pass. `rai gate check --all` should also distinguish missing scoped
   invocation context from product failures.
4. **Capability gained:** the project can now distinguish terminal-incomplete
   dispositions from active backlog while still rejecting `Complete`, unknown
   states, and missing disposition evidence.

## Patterns

- Added: `PAT-L-1267` — canonical vocabulary, executable contract, and
  fail-closed tests must migrate atomically.
- Reinforced: `BASE-001` (+1, TDD), `BASE-020` (+1, Jidoka), `BASE-043`
  (+1, semantic assertions).

## Remaining Review Context

The four code gates pass. Architecture review is intentionally not claimed by
this retrospective; `gate-ar-bugfix` must be satisfied in its dedicated review
context before bug closure.
