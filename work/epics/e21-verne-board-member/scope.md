# Epic Scope: E21 — Verne Harnish Board Member

**Status:** Draft
**Dependencies:** E19 (grafo de conocimiento del libro)
**Tamaño:** XL

## In Scope
- **Alma de Verne** (`miembro-board/verne-harnish.md`):
  - Su framework: Rockefeller Habits, 4 Decisions, Power of One
  - Sus preguntas características: "¿Cuál es tu ROC?", "¿Tienes un Daily Huddle?", "¿Quién es tu Core Customer?"
  - Su lente: prioriza cash flow, simplicidad, ejecución, hábitos
  - Sus sesgos: prefiere acción sobre análisis, estructuras simples, accountability clara
  - Sus principios no negociables: "No surprises", "Keep things simple", "Daily Huddle every day"
- **Agente de revisión**: Verne revisa tus dailys y da observaciones
- **Consulta directa**: "Verne, ¿qué opinas de mi strategy?"
- **Integración con ciclo de sesión**: al cerrar sesión, Verne puede dar su perspectiva
- **Modo board completo**: Verne debate contigo sobre decisiones específicas

## Out of Scope
- Ingresar el libro (E19)
- Conectar skills a dashboards (E20)
- Crear otros miembros del board (Hormozi, Collins, etc. — futuras épicas)
- Procesamiento de audio/video (solo texto)

## Dependencias
- E19 (conocimiento estructurado del libro en el grafo)
- E18 (infraestructura: server, sesiones, SQLite, CLI)
- El alma debe basarse ESTRICTAMENTE en el libro — no inventar

## Done Criteria
- [ ] `miembro-board/verne-harnish.md` completo con framework, preguntas, lente, sesgos, principios
- [ ] Verne puede analizar un daily y dar observaciones
- [ ] Verne puede responder a "¿qué opinas de X?" con coherencia
- [ ] Integrado con escala-inicia: Verne recibe contexto de la sesión
- [ ] Los skills pueden consultar "¿qué diría Verne sobre X?"
- [ ] Tests: respuestas de Verne son coherentes con el libro

## Implementation Plan

> Added by `/rai-epic-plan` — 2026-05-30

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale |
|:-----:|-------|:----:|--------------|-----------|-----------|
| 1 | S21.1 — Alma de Verne | S | E19 (grafo del libro) | M1 | Foundation: sin el personaje documentado no se construye nada |
| 2 | S21.2 — Consulta directa | M | S21.1 | M1 | **Walking skeleton E2E**: crear el alma + poder preguntarle "¿qué opinas de X?" |
| 3 | S21.3 — Revisión de dailys | M | S21.2 | M2 | Core MVP: Verne analiza un daily y da observaciones consistentes con Rockefeller Habits |
| 4 | S21.4 — Integración con ciclo de sesión | S | S21.2 | M2 | Core MVP: Verne participa al cerrar sesión con perspectiva basada en contexto |
| 5 | S21.5 — Modo board completo | M | S21.3, S21.4 | M3 | Feature complete: debate contextual completo sobre decisiones estratégicas |
| 6 | S21.6 — Tests de coherencia | S | S21.2 | M4 | Epic complete: verificación formal contra el libro |

### Milestones

| Milestone | Stories | Success Criteria |
|-----------|---------|------------------|
| **M1: Walking Skeleton** | S21.1, S21.2 | Alma documentada + endpoint `/api/verne/ask` responde con coherencia |
| **M2: Core MVP** | +S21.3, S21.4 | Verne revisa dailys + participa en cierre de sesión |
| **M3: Feature Complete** | +S21.5 | Modo board completo operativo (debate multi-turno) |
| **M4: Epic Complete** | +S21.6 | Tests pasan + done criteria verificados + retrospective |

### Sequencing Strategy

**Walking skeleton (risk-first)**: Probar la arquitectura con el camino E2E más corto — documentar el alma, luego preguntarle algo. Esto valida que la integración con el grafo de conocimiento (E19) funciona antes de invertir en features complejas.

**Dependency-driven**: S21.3 y S21.4 dependen de S21.2 (necesitan el mecanismo de consulta). S21.5 necesita ambos. S21.6 puede empezar después de S21.2.

### Parallel Work Streams

```
Tiempo →
Stream 1 (Crítico):  S21.1 ──► S21.2 ──► S21.3 ──► S21.5
                                         ↓
Stream 2 (Paralelo):                   S21.4 ──────► merge
                                                       ↓
Stream 3 (Paralelo):         S21.6 ────────────────────► merge
```

**Merge points:**
- Después de S21.2 (M1): base sólida — se abre paralelismo
- Antes de S21.5: merge de S21.4 y S21.6

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S21.1 — Alma de Verne | S | Done | ~15m | 1.0 | ✅ `miembro-board/verne-harnish.md` — 266 líneas, 43 entidades del grafo |
| S21.2 — Consulta directa | M | Done | ~20m | 1.0 | ✅ Handler + API + CLI, 12 tests |
| S21.3 — Revisión de dailys | M | Done | ~10m | 1.0 | ✅ review_daily(), 5-element checklist, 15 tests |
| S21.4 — Integración ciclo sesión | S | Pending | — | — | Hook en cierre de sesión para perspectiva de Verne |
| S21.5 — Modo board completo | M | Pending | — | — | Debate multi-turno con contexto acumulado |
| S21.6 — Tests de coherencia | S | Pending | — | — | Tests contra libro: preguntas conocidas, respuestas esperadas |

### Sequencing Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| El alma de Verne se inventa en lugar de basarse estrictamente en el libro | H/M | Cross-reference constante contra entidades del grafo E19; criterio de aceptación: toda afirmación debe tener origen verificable en el grafo |
| Walking skeleton sin LLM local — Verne necesitará un modelo para generar respuestas coherentes | M/H | Evaluar opciones: (1) integración con OpenAI API vía handler, (2) prompt estructurado desde el alma + contexto del grafo, (3) delegación a skill de Hermes |
| S21.3 y S21.5 requieren parsing de lenguaje natural (dailys, decisiones) que puede ser impreciso sin LLM | M/M | Comenzar con templates estructurados (daily en formato JSON); modo board como conversación guiada con preguntas predefinidas de Verne |
