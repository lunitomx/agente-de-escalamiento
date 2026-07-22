# S36.4 Governance Identity Integration Summary

Date: 2026-07-21
Source HEAD before evidence commit: `681e57c62bd821c150e3d1398c86e958da121af9`
Result: **PASS**

## Contract receipt

- Two consecutive CLI runs after T4 produced byte-identical JSON and Markdown.
- External JSON SHA-256:
  `d88e99640379124f0bf6b9e5f6385329d65af112a781ade27fe7f3a857b62923`.
- External Markdown SHA-256:
  `10dce04122ca8af5db13f3dac1fd3b971ee9aee72483bdb9bf4f00d911cb7d7a`.
- Semantic closure-policy SHA-256:
  `e5b9e9207fce7bbacd3af0a9e93368d6ccf38f979932d10360a2063924f8f023`.
- Semantic identity-policy SHA-256:
  `eb62cd804fa3b0559d20394e27be583b6daa445c6619938b43d4a1a92d052d52`.
- The versioned T4 JSON and Markdown are 1,762 bytes combined and contain no
  root, URL, source text, raw error, or subprocess transcript.

## Real repository and graph

- Canonical scopes present: `10/10`.
- Legacy alias scopes present: `0`.
- Duplicate policy-derived graph IDs: `0`.
- Installed strict graph build: `PASS`.
- Epic concepts indexed: `38`; all concepts indexed: `226`.
- Canonical graph queries: `10/10`, one exact `epic-eNNNN` concept for each of
  E1801, E1802, E1901, E1902, E2001, E2002, E2101, E2102, E2201, and E2202.
- Bare E18, E19, E20, E21, and E22 each returned `ambiguous` with their exact
  sorted two-candidate set. No first-folder resolution occurred.

## Historical integrity

- Pre-story S36.2 evidence tree:
  `2d415d36caeadb671e6fedfa933189c409677b8b`.
- Current S36.2 evidence tree:
  `2d415d36caeadb671e6fedfa933189c409677b8b`.
- Immutable baseline JSON SHA-256:
  `3ae688c34b8cb13dcf96bd72198aeee6e4eace0a432b413cc654d1c279943dce`.
- Residual old paths are limited to declared aliases and named historical
  evidence. One current retrospective cross-link was migrated to E1901.

## Verification and importer audit

- Governance contract tests: `PASS` (`76` cases).
- Epic closure consumer tests: `PASS` (`28` cases).
- Full-project lint, format, and type gates: `PASS`.
- Schema sum: `PASS`, schema version `32`, migrations `32`.
- Relevant test importers found: `2`; both were changed, inspected, and passed.
- Orphaned unchanged test importers: `0`.
- One initial display-only ambiguity command had a quoting error; the isolated
  resolver rerun passed all five cases. Product code and repository data were
  not involved in that command-construction defect.

## Boundaries preserved

- No installed RaiSE package, Git history, remote, public candidate, hosted
  runtime, database schema, or external service was modified.
- No push or publication occurred.
- Runtime and evidence remain local-only. Drive/OneDrive remain optional
  filesystem sharing locations; SQLite remains outside synchronized folders.
