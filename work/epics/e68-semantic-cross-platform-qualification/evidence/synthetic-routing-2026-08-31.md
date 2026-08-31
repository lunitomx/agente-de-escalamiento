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

- Cliente: `2.1.251`, cuenta Team `Humansys`, ejecución sin persistencia.
- Resultado: JSON válido con 6/6 rutas esperadas:
  - A: `diagnose-primary-constraint`
  - B: `build-leader-oppp`
  - C: `build-vision-summary`
  - D: `set-quarterly-priority`
  - E: `install-meeting-rhythm`
  - F: `run-quarterly-review`
- La primera ejecución tras renovar OAuth falló antes de enviar inferencia por
  sintaxis inválida de `--tools ''`; el reintento sin ese parámetro ejecutó una
  única inferencia y produjo el resultado anterior.
## Interpretación

La ruta sintética es equivalente entre Codex CLI y Claude Code: ambos
produjeron las seis intenciones esperadas. Esta evidencia elimina el bloqueo
de autenticación y permite continuar S68.3/S68.4, pero por sí sola no cierra
E68: aún faltan receipts estructurados, reporte de paridad y el piloto humano
trimestral definidos en las historias restantes.
