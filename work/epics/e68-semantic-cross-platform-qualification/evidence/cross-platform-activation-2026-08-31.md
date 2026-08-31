# Evidencia S68.4 — activación cross-platform — 2026-08-31

## Condiciones

Suite `escala.mvp.activation.v1`, nueve casos sintéticos, sesiones efímeras,
sin archivos de empresa, herramientas ni contenido identificable.

## Codex

- Cliente: `codex-cli 0.151.0`, modelo `gpt-5.6-terra`.
- Sesión: `01a05953-b3cc-7350-93c3-cc59a6cd9a48`.
- Resultado normalizado: precision `1.0`, recall `1.0`.

## Claude

- Cliente: `Claude Code 2.1.251`, cuenta Team `Humansys`.
- Resultado normalizado: precision `1.0`, recall `1.0`.

## Diferencias declaradas

En ACT-009 Codex devolvió el alias `quarterly-priority` y Claude devolvió el
intent canónico `set-quarterly-priority`. Ambos resuelven a
`procedure.set-quarterly-priority`; por ello la diferencia semántica es cero.

## Límite

El resultado no constituye A/B de capabilities instaladas ni aprobación de un
piloto humano. Es evidencia de routing sintético real en ambas plataformas.
