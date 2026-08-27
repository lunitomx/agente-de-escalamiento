# Design E74 — Colaboración local basada en archivos

## Topología propuesta

```text
<shared-root>/companies/<company-id>/
  manifest.yaml              # identidad, schema y política
  state/profile.yaml         # aprobado, no secretos
  state/facts/*.yaml         # procedencia, periodo, owner, revisión
  state/decisions/*.yaml     # decisión, acción, cadencia, aprobación
  artifacts/<date>-*.md      # reportes aprobados/redactados
  history/*.jsonl            # append-only
  proposals/*.yaml           # borradores y conflictos pendientes

<local-root>/escala/<installation-id>/
  config/                    # secretos/configuración local
  cache/<company-id>.sqlite  # reconstruible, nunca compartida
```

## Escritura

Un perfil propone un cambio estructurado. `escala` valida empresa, schema,
owner, versión base y consentimiento. Si la versión cambió, crea un conflicto
legible; no intenta fusionar campos financieros o decisiones. Un owner humano
aprueba/rechaza/reconcilia, y el histórico conserva ambas versiones.

## Lectura

Cada agente recibe `company-id` y sólo el paquete mínimo aprobado. No puede
consultar otra carpeta ni usar una cache cuyo manifest no coincida.

## Evaluación

- contador propone hecho Cash y director aprueba;
- estrategia y Cash trabajan empresas distintas;
- dos ediciones concurrentes del mismo hecho;
- cache borrada y reconstruida;
- archivo YAML corrupto y archivo SQLite introducido en shared root.
