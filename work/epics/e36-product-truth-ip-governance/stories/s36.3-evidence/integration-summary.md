---
story_id: "S36.3"
evidence_type: "live_private_public_boundary"
observed: "2026-07-21"
status: "pass"
---

# S36.3 Live Boundary Integration Summary

## Verdict

The finished local CLI produced a passing, sanitized receipt from committed
private source `44ddf72f55e4dc9b6601e968045f8c25179f738c`, the immutable S36.2
baseline, and the existing dirty public candidate. The scan reported no errors,
did not mutate either scan subject while observing it, and did not write inside
the public candidate.

This is a source-boundary receipt, not an export allowlist or release decision.
The separate existing public candidate remains explicitly unresolved.

## Source Binding

| Evidence | Value |
|---|---|
| S36.2 baseline SHA-256 | `3ae688c34b8cb13dcf96bd72198aeee6e4eace0a432b413cc654d1c279943dce` |
| S36.3 policy SHA-256 | `2fff50579bbbd4684a114bdb08739b5fbe8f9258c2ec1582782fec14ef810412` |
| Verifier source commit | `44ddf72f55e4dc9b6601e968045f8c25179f738c` |
| Receipt status | `pass` |

## S36.2 to S36.3 Delta

| Surface | S36.2 | S36.3 live result |
|---|---|---|
| Raw asset in worktree | absent | absent |
| Raw asset in canonical `HEAD` | present | absent |
| Raw asset in reachable history | historical | historical |
| Candidate-public private source | findings present | zero findings; 285 tracked candidate paths inspected |
| Required candidate files unreadable | 7 worktree / 8 `HEAD` | zero worktree / zero `HEAD` |
| Existing public candidate | unresolved, 17 dirty entries | unresolved, 17 dirty entries, fingerprint unchanged |

The stricter S36.3 policy reports 209 unresolved findings in the existing
public candidate. That count is evidence of candidate risk, not a regression in
the repaired private source and not a claim that the public repository was
cleaned.

## Non-Mutation Proof

- Public candidate `HEAD` remained
  `7e62accc7a4df009b8a68abf0bb178ad02c963f0`.
- Its dirty-entry count remained `17`.
- Status, worktree, config, index, and refs SHA-256 values were byte-identical
  before and after observation.
- The private scanner's internal before/after fingerprints were also
  byte-identical. The only later private-tree writes were these explicitly
  approved versioned evidence files.

## Determinism and Evidence Bounds

Two consecutive CLI runs with output paths outside the scanned repository were
byte-identical:

- JSON SHA-256:
  `cf295a857cfb42f8e30592b98abe115da313abcd68be3c188a6fbbf909de569a`
- Markdown SHA-256:
  `041fac1d8f1d1ed962a142209685391ff551fc7b6a32913d067bc2f6767bfff4`

The committed Markdown is 1,824 bytes, below the 32 KiB limit. Determinism was
measured outside the scanned root because a receipt stored inside that root
necessarily changes the whole-worktree fingerprint it records. The receipt
contains hashes, bounded counts, safe locators, and grouped findings; it does
not contain repository roots, remote URLs, matched values, excerpts, or
command transcripts.

## Classification Boundary

| Disposition | Count | Set SHA-256 |
|---|---:|---|
| Candidate public | 285 | `05ef611554dc8d02680642fd8be44bc5905bb4eeda9a4d44c5a6649ce45187ba` |
| Denied | 829 | `d4031ef2a40aa9bf590bde42c97066aae9a9dc119970e3ca80f6cdc4f53d7927` |
| Not eligible | 66 | `8b43daa1b5a06c7ca64d653576ad3e76ee4f0534505fe94d7d373208f930df68` |

S36.5 may consume these hashes and the policy, but must construct its own
explicit allowlist. No candidate-public count is permission to publish.
