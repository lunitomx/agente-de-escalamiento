<!-- ESCALA:BEGIN -->
# ESCALA for Claude Code

## Boundary

Use `{{ESCALA_SKILL_PATH}}` as the single public entrypoint. Its portable
capability contract is `{{ESCALA_CAPABILITY_CATALOG}}`. Do not turn internal
material into additional public commands or add a separate interpretation
layer here.

## Local runtime

{{ESCALA_PYTHON}}

## Local operation

Load only local context the business explicitly consents to use. Preserve
approved history, propose a state change before writing it, and explain any
missing evidence in business language.

## Extensions

Remote extensions are disabled by default. Do not create external
configuration, transmit business context, or assume a service is available
without an explicit company-level authorization.
<!-- ESCALA:END -->
