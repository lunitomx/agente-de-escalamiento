# Public Boundary Receipt

- Status: `pass`
- Policy SHA-256: `2fff50579bbbd4684a114bdb08739b5fbe8f9258c2ec1582782fec14ef810412`
- Verifier source commit: `44ddf72f55e4dc9b6601e968045f8c25179f738c`
- Baseline SHA-256: `3ae688c34b8cb13dcf96bd72198aeee6e4eace0a432b413cc654d1c279943dce`
- Public candidate: `legacy_findings_unresolved`
- Public candidate finding count: `209`
- Private repository unchanged: `yes`
- Public candidate unchanged: `yes`

## Raw reference state

- Worktree: `absent`
- Git HEAD: `absent`
- Git history: `historical`

## Path classifications

- Candidate public: `285` (`05ef611554dc8d02680642fd8be44bc5905bb4eeda9a4d44c5a6649ce45187ba`)
- Denied: `829` (`d4031ef2a40aa9bf590bde42c97066aae9a9dc119970e3ca80f6cdc4f53d7927`)
- Not eligible: `66` (`8b43daa1b5a06c7ca64d653576ad3e76ee4f0534505fe94d7d373208f930df68`)

## Surfaces

- `private_worktree`: inspected=`true`, tracked=`1180`, candidate_public=`285`, unscanned_required=`0`
- `private_head`: inspected=`true`, tracked=`1180`, candidate_public=`285`, unscanned_required=`0`
- `private_history`: inspected=`true`, tracked=`1324`, candidate_public=`0`, unscanned_required=`0`
- `public_candidate_head`: inspected=`true`, tracked=`173`, candidate_public=`173`, unscanned_required=`0`

## Finding groups

- `public.author_identity` | `public_candidate_head` | `prohibited_text` | count=`16`
- `public.execution_identity` | `public_candidate_head` | `prohibited_path` | count=`2`
- `public.execution_identity` | `public_candidate_head` | `prohibited_text` | count=`8`
- `public.product_identity` | `public_candidate_head` | `prohibited_text` | count=`86`
- `public.provenance` | `public_candidate_head` | `prohibited_yaml_key` | count=`78`
- `public.source_attribution` | `public_candidate_head` | `prohibited_text` | count=`19`

## Errors

- None
