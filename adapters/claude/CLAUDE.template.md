# ESCALA for Claude Code

## Boundary

Use the portable core at `../../escala-skills/escala/SKILL.md` as the single
public entrypoint. Do not turn internal material into additional public
commands, and do not add a separate interpretation layer here.

## Local operation

Load only local context the business explicitly consents to use. Preserve
approved history, propose a state change before writing it, and explain any
missing evidence in business language.

## Extensions

Remote extensions are disabled by default. Do not create external
configuration, transmit business context, or assume a service is available
without an explicit company-level authorization.
