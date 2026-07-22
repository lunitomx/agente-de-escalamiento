# S36.5 Real M3 Integration Summary

## Outcome

`PASS` for technical artifact qualification from immutable source commit
`faad022c3e42786178bada757f19101b9a292d83`.

Legal review remains `required`, approval evidence remains absent, and
publication authorization remains `false`. The generated product is local-only;
this run did not publish, push, copy to the public candidate, invoke a hosted
runtime, call Drive/OneDrive APIs, or synchronize a SQLite database.

## Sequence executed

1. Captured strong private and public-candidate fingerprints.
2. Built the same full source commit into two distinct new system-temporary
   directories through the builder CLI.
3. Invoked the separate verifier CLI against both artifacts.
4. Proved artifact-tree, manifest, build-receipt, stdout, and verification-
   receipt byte identity.
5. Copied only temporary artifact B into a third temporary tree, changed one
   byte in one known payload, and proved the independent verifier failed only
   with `artifact.hash_mismatch`, exit code `3`, safe output, and no receipt.
6. Recaptured strong fingerprints and proved both repositories unchanged.

## Jidoka repair

The first real run from `0b5cd5e64ce7f2d6a8a60d003de31339ba0e695e`
stopped with one `public.product_identity` violation in selected
`pyproject.toml`. A focused RED reproduced it. Commit `faad022` removed the
private control-plane name from portable metadata while retaining a generic
hidden-directory lint exclusion. All focused gates passed before the second
real run. The failed run is recorded as diagnostic truth, not PASS evidence.

## Result

The exact 264-file staged artifact passes all ten named technical checks. This
proves that a clean local artifact can be assembled and independently verified;
it does not grant legal approval or authorize publication.
