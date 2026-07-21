# Public Candidate Read-Only Witness

- Result: `unchanged`
- Label: `public_candidate`
- HEAD before/after: `7e62accc7a4df009b8a68abf0bb178ad02c963f0`
- Branch before/after: `main`
- Dirty entry count before/after: `17`
- Status SHA-256 before/after:
  `7de1ccaa65300cc786cc4215cb83c3447d6436c78340be9113b66a94c908f94b`
- Worktree SHA-256 before/after:
  `900d14d780d178c44369fb7b749a37c5481fa3f69c140392808ad1bb86cc4a53`
- Local config SHA-256 before/after:
  `35da478707037efd1d45f3d62b7c5bf24d6c217a3a35077caa68be748b9e268c`
- Index SHA-256 before/after:
  `c1c4c25e3c87868433331c1416fbaa2059d4c156d9d6c669fda5e5e1e0a8ebfd`
- Refs SHA-256 before/after:
  `e3eb68d7fd9aca228fc53d3b467d38fcef69f0bdf0839e177219f7f1de53f24e`

Review strengthened the witness after discovering that HEAD/status alone could
miss a content change with the same porcelain shape. The final contract hashes
the complete non-`.git` worktree plus local config, logical index, and refs while
forcing `GIT_OPTIONAL_LOCKS=0`. It contains no local root, filename, or value.
Equality across all fields proves the candidate remained unchanged during the
strong before/after review window and reinforces the earlier read-only witness.
