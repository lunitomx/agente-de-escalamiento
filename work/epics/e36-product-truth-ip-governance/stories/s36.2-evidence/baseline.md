# Exposure Inventory Receipt

- Scan status: `complete`
- Policy SHA-256: `7eec173c0b2a132b15a3a1dfda8cfdeeac36e27621a1bf5a70a0fe37b61c7b0c`
- Verifier source commit: `e863f781600a99c476e0f1182ddcc8552983b7e3`
- Distribution default: `not_eligible`
- Generated staging: `not_built`
- Tracked path count: `1175`
- Tracked path set SHA-256: `12f6baae02073f005bd26efa5901ae19582ee0863fc04bb48a4e8772ee84feca`
- Private repository mutation check: `pass`
- Public candidate mutation check: `pass`

## Risk summary

- `critical`: `27`
- `high`: `598`
- `medium`: `1501`
- `low`: `0`
- `info`: `0`

## Surfaces

- `worktree`: inspected=`true`, items=`1175`, unscanned=`7`
- `git_head`: inspected=`true`, items=`1175`, unscanned=`8`
- `git_history`: inspected=`true`, items=`1304`, unscanned=`0`
- `local_git_config`: inspected=`true`, items=`1`, unscanned=`0`
- `distribution_candidate`: inspected=`true`, items=`1175`, unscanned=`0`
- `public_candidate`: inspected=`true`, items=`173`, unscanned=`0`

## Finding groups

- `reference.raw_asset` | `worktree` | `raw_reference` | `critical` | `absent` | `remove_in_s36_3` | count=`1`
- `reference.derived_material` | `worktree` | `derived_reference` | `high` | `present` | `review_in_s36_3` | count=`12`
- `public.methodology_attribution` | `worktree` | `public_vocabulary` | `high` | `present` | `review_in_s36_3` | count=`255`
- `public.methodology_attribution` | `worktree` | `public_vocabulary` | `high` | `absent` | `review_in_s36_3` | count=`1`
- `private.company_state` | `worktree` | `private_data` | `critical` | `present` | `block_in_s36_5` | count=`12`
- `internal.raise_state` | `worktree` | `internal_path` | `medium` | `present` | `block_in_s36_5` | count=`10`
- `internal.work_evidence` | `worktree` | `internal_path` | `medium` | `present` | `block_in_s36_5` | count=`486`
- `reference.raw_asset` | `git_head` | `raw_reference` | `critical` | `present` | `remove_in_s36_3` | count=`1`
- `reference.derived_material` | `git_head` | `derived_reference` | `high` | `present` | `review_in_s36_3` | count=`12`
- `public.methodology_attribution` | `git_head` | `public_vocabulary` | `high` | `present` | `review_in_s36_3` | count=`256`
- `private.company_state` | `git_head` | `private_data` | `critical` | `present` | `block_in_s36_5` | count=`12`
- `internal.raise_state` | `git_head` | `internal_path` | `medium` | `present` | `block_in_s36_5` | count=`10`
- `internal.work_evidence` | `git_head` | `internal_path` | `medium` | `present` | `block_in_s36_5` | count=`486`
- `reference.raw_asset` | `git_history` | `raw_reference` | `critical` | `historical` | `remove_in_s36_3` | count=`1`
- `reference.derived_material` | `git_history` | `derived_reference` | `high` | `historical` | `review_in_s36_3` | count=`12`
- `internal.work_evidence` | `git_history` | `internal_path` | `medium` | `historical` | `block_in_s36_5` | count=`509`
- `public.methodology_attribution` | `public_candidate` | `public_vocabulary` | `high` | `present` | `review_in_s36_3` | count=`50`

## Errors

- None
