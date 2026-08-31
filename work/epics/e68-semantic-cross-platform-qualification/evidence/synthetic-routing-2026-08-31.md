# Evidencia sintética de routing — 2026-08-31

## Condiciones

Se usaron seis solicitudes sintéticas, una por capacidad MVP, sin archivos,
herramientas ni datos de empresa. La respuesta requerida fue JSON de
intenciones normalizadas.

## Codex CLI

- Cliente: `codex-cli 0.149.0`, modelo reportado `gpt-5.6-terra`.
- Sesión efímera: `01a0568e-ff94-7931-a3ca-d21c3ccbaa1b`.
- Sandbox: read-only.
- Resultado: 6/6 rutas esperadas, JSON válido y sin tools.

## Claude Code

- Cliente: `2.1.241`, ejecución sin persistencia y sin tools.
- Resultado: no hubo inferencia ni clasificación.
- Motivo observado: `OAuth session expired and could not be refreshed`.

## Interpretación

Es evidencia parcial, no calificación cross-platform. No permite declarar
paridad ni cerrar S68.4/E68. Tras renovar OAuth de Claude, debe repetirse la
misma suite y registrar ambos resultados en S68.3/S68.4.
