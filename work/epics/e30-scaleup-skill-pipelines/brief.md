# Epic Brief: E30 - ScaleUp Skill Pipelines

## Hypothesis

ScaleUp already has 39 useful `scaleup-*` skills, but most domain entrypoints still behave like routers that recommend the next command. Emilio's session insight is that consistency improves when a complete artifact is produced by a pipeline of small skills, each with its own context, budget, model fit, and quality gate.

If we define canonical ScaleUp pipelines over the existing skills, users can move from isolated skill calls to governed workflows without rewriting the skill catalog.

## Success Metrics

- A canonical pipeline registry exists for the main ScaleUp workflows.
- Every pipeline phase references an existing `scaleup-*` skill.
- Each pipeline declares inputs, outputs, stop conditions, gates, and evidence.
- A code validator catches missing skills, duplicate phases, and malformed gates.
- Existing `scaleup-start` and `scaleup-close` orchestration patterns are reused instead of replaced.

## Appetite

Medium. This epic should formalize and validate orchestration first. Runtime automation or a new pipeline engine belongs in a later story only after the registry contract is stable.

## Rabbit Holes

- Do not create new coaching methodology content.
- Do not rewrite all SKILL.md files in one pass.
- Do not build a generic workflow engine before the ScaleUp registry proves the shape.
- Do not change user data under `.scaleup/my-company/`.

