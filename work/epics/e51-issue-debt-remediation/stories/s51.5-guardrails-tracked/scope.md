# S51.5 Scope

## In Scope
- Force-track `governance/guardrails.md` in git despite the `governance/` `.gitignore` rule.
- Verify the boundary test passes.

## Out of Scope
- Modifying other governance files.
- Changing `.gitignore` broadly.

## Done when
- `governance/guardrails.md` appears in `git ls-files`.
- `git check-ignore governance/guardrails.md` reports the file is not ignored.
- `tests/test_public_boundary.py` passes.
