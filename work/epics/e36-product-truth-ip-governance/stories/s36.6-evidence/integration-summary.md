# S36.6 Real Baseline Integration Summary

## Qualified source

- Source commit: `e27594395cdba0087f6d7f42e8f36ce2ed3dd4bf`
- Source tree: `2748bfcf6aa994ec80e96587079fc05aa40334a0`
- Ledger semantic SHA-256:
  `1dbe5c06bdba1488dfeccabd95e99e2936977cd6b1759fb66fd66851a364b8c9`
- Rendered ledger SHA-256:
  `4c35c44f737afcd1cc8dbae31723074193dccbf5968a8e4b90bebd2c4324fa17`

## Double-run evidence

Two independent local baseline CLI processes used the same committed ledger
and current typed authorities in separate new system-temporary directories.

- Both exit codes: `0`.
- JSON receipt A/B SHA-256:
  `fbff51a338fe0bef8a0205ead1561e4e9c50136c16bedf2826b30fbd81acf5ea`.
- Markdown receipt A/B SHA-256:
  `376e832e4c46dafd5775ee37788c0ccea94464eb71edd71ba6d5c397471c47ac`.
- JSON stdout A/B SHA-256:
  `fbff51a338fe0bef8a0205ead1561e4e9c50136c16bedf2826b30fbd81acf5ea`.
- JSON, Markdown, stdout, and empty stderr are byte-identical between runs.
- Canonical ledger Markdown is byte-identical to a fresh renderer result.

## Truthful acceptance state

- Contract status: `pass`.
- Mission readiness: `unproved`.
- Epics inventoried: `6`.
- Requirements inventoried: `42`.
- Proved: `0`.
- Unproved: `42`.
- Every blocker is exactly `evidence.missing`; no future epic or product
  capability is claimed complete.

Readiness mode returned exit `2` both for filtered `E37` (`0/7`) and the full
mission (`0/42`). A deliberately corrupt temporary YAML returned exit `1`,
empty stdout, and the one fixed safe error. It emitted neither its private
sentinel name nor a machine path, URL, source value, or raw exception.

## Authority and non-mutation proof

- Closure disposition semantic SHA-256:
  `e5b9e9207fce7bbacd3af0a9e93368d6ccf38f979932d10360a2063924f8f023`.
- Epic identity semantic SHA-256:
  `eb62cd804fa3b0559d20394e27be583b6daa445c6619938b43d4a1a92d052d52`.
- Public-export semantic SHA-256:
  `3faf9e3e350ef10a17f3e8634df7fbc6a8ed15dfd6e9cbe99e1769c26ada2cea`.
- Runtime and authoritative data remain on the installer machine.
- Team exchange remains ordinary filesystem documents only.
- Authoritative SQLite synchronization remains forbidden.
- Human legal review remains required and publication remains unauthorized.
- HEAD, committed tree, and worktree status were identical before and after the
  real observations.
- No remote, public candidate, hosted service, Drive/OneDrive API, SQLite,
  push, publication, or external system was mutated.

This receipt supersedes the pre-review baseline only as current qualification
evidence. The earlier receipt remains auditable in Git history. The rerun was
mandatory because review changed the human renderer and reviewable-disposition
contract; no stale receipt was relabeled as current.
