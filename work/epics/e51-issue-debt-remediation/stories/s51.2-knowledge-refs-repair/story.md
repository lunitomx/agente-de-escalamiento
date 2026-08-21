# S51.2: Knowledge References Repair

## Problem
GitHub issue #2 reports that 8 `escala-skills` SKILL.md files reference `.escala/knowledge/**/*.md` files that do not exist. The real content lives in `conocimiento/**/*.yaml` with shorter names. Skills degrade because they cannot load the intended knowledge.

## Root Cause
During the ScaleUp→ESCALA migration, knowledge files were renamed from descriptive `.md` to short `.yaml` and moved to `conocimiento/`. The SKILL.md references were never updated.

## Goal
Repoint every broken reference to the real `.yaml` source of truth. No content duplication.

## Acceptance Criteria
- [ ] Each of the 8 listed references points to an existing file.
- [ ] `escala-people-organigrama` reference to `face.md` is also repaired.
- [ ] A script or test fails if a SKILL.md references a non-existent knowledge path.
- [ ] All existing tests pass.

## Tasks
1. Map every broken `.escala/knowledge/**/*.md` reference to its real `conocimiento/**/*.yaml` file.
2. Edit the SKILL.md files in `escala-skills/`.
3. Add a regression test / audit script that verifies knowledge references.
4. Run gates.

## Related
- GitHub issue #2
