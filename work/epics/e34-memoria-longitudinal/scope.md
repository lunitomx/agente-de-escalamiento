# Epic Scope: E34 — Memoria Longitudinal

**Status:** Draft
**Dependencies:** E31 (board proactivo usa memoria)
**Tamaño:** S (2 historias, ~3h)
**Origen:** Visión de coach — el coach que no se acuerda de ti no es coach. El memory engine ya existe. Hay que usarlo para algo que el usuario sienta.

## Visión

"Me acuerdo de ti, Eduardo. Sé que en Q4 2025 casi te quedas sin cash. Sé que tu VP de Ventas renunció en marzo y todavía no has contratado reemplazo. Sé que cada Q3 tus cuentas por cobrar se disparan — ¿quieres que te ayude a prevenir eso este año?"

El memory engine (`memory_engine.py`) ya guarda facts con trust scoring. El graph engine ya resuelve entidades. Esta épica los usa para dos cosas que el usuario SÍ va a sentir: alertas de patrones repetidos y recomendaciones basadas en historia.

## Stories

| Story | Size | Qué |
|-------|:----:|-----|
| **S34.1 — Perfil longitudinal del negocio** | M | Escala mantiene un timeline trimestral: qué pasó en Q1, Q2, Q3... KPIs, decisiones, crisis, contrataciones. "Tu CCC en Q1 2025: 45 días. Q1 2026: 62 días. Tendencia: subiendo." |
| **S34.2 — Detección de patrones + alertas** | M | Escala detecta ciclos: "Tus problemas de cash siempre empiezan en Q3. Estamos en junio — ¿empezamos a preparar?" O: "Las últimas 3 veces que tu NPS bajó, fue 2 meses después de contratar un VP nuevo. ¿Patrón de onboarding débil?" |

## Done Criteria

- [ ] S34.1: `perfil` comando devuelve timeline con KPIs trimestrales y eventos clave
- [ ] S34.2: alerta automática cuando detecta patrón repetido (mismo problema 2+ trimestres)
