# Epic Scope: E31 — Board Proactivo Trimestral

**Status:** Draft
**Dependencies:** E29 absorbida (templates Verne ya en YAML), E30 (data real disponible)
**Tamaño:** M (4 historias, ~8h)
**Origen:** Visión de coach — el board no espera a que el CEO pregunte. Se reúne solo cada 3 meses.

## Visión

El board ficticio deja de ser reactivo ("pregúntale a Verne algo") y se vuelve proactivo. Cada trimestre, el board se "reúne" (runtime de Claude Code/Codex), revisa TODA la data acumulada en memoria/, y produce un paquete de decisiones. El empresario solo revisa, ajusta, y ejecuta.

## Historias preparatorias

Antes del board proactivo, los templates de Verne que hoy están hardcodeados en Python deben moverse a YAML para que el runtime trimestral pueda usarlos sin tocar código. Esto se absorbe de la extinta E29.

## Stories

| Story | Size | Qué |
|-------|:----:|-----|
| **S31.0 — Templates Verne a YAML** | S | Mover `_VERNE_TEMPLATES` y `_DAILY_CHECKLIST` de `verne_handler.py` a `conocimiento/coaching/`. Cargar con `yaml.safe_load()`. Tests existentes pasan sin cambios. |
| **S31.1 — Modo proactivo en VerneHandler** | M | Extender VerneHandler con método `board_session()`: revisa memoria/, knowledge graph, datos de E30. No espera pregunta — genera análisis. |
| **S31.2 — SWT automático trimestral** | M | Runtime que lee memoria/, worksheets, KPIs, y genera Strengths, Weaknesses, Trends con evidencia citada. "Weakness: CCC subió 17 días — ver sesión S-X-260315." |
| **S31.3 — Propuesta de Prioridad #1 + Tema** | M | Basado en el SWT, el board propone la Prioridad #1 del siguiente trimestre con justificación numérica. Sugiere Tema, Critical Number y meta. |
| **S31.4 — Acta de board + Carta al CEO** | S | Output final: acta estructurada (decisiones, votos, dissents) + carta estilo Verne (directa, a veces incómoda). "Eduardo, tu equipo está bien, tu cash está bien. El problema es que no has decidido quién es tu Core Customer." |

## Done Criteria

- [ ] S31.0: `verne_handler.py` < 350 LOC. Templates en YAML.
- [ ] S31.1: `board_session()` funciona sin pregunta del usuario
- [ ] S31.2: SWT generado cita fuentes reales (sesiones, worksheets, KPIs)
- [ ] S31.3: Prioridad #1 propuesta con justificación numérica
- [ ] S31.4: acta + carta generadas en < 2 min de runtime
