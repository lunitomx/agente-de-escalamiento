# Epic Scope: E22 — Full System Audit (3 Empresas × Todos los Skills)

**Status:** In Progress
**Dependencies:** E14 (Cash dashboards), E15 (Strategy dashboards), E16 (People dashboards), E17 (Execution dashboards), E21 (Verne)
**Tamaño:** L

## Buyer Personas

### P1: Don Roberto — Carnicería "El Buen Corte"
- 3 sucursales, 8 empleados, $450k MXN/mes
- Gerentes = familiares que "no rinden". Sin procesos, sin reuniones
- Corte de efectivo quincenal. Don Roberto decide todo él solo
- **Tech level:** Básico. Usa WhatsApp y calculadora.
- **Necesita:** Alguien que le diga QUÉ hacer, no bonitos dashboards

### P2: Ana y Carlos — "Estrategia 360 Consultores"
- 15 consultores, $1.2M MXN/mes. Cobran $3,500/hr
- Clientes tardan 60 días en pagar. Consultores senior se queman.
- Tienen weekly meetings pero duran 2h sin WWW
- **Tech level:** Medio. Usan CRM, Excel, Google Workspace
- **Necesita:** Orden en ejecución y retención de talento

### P3: CEO — "CloudScale Technologies" (SaaS, vende licencias como RAISE)
- 28 empleados, $3.5M MXN/mes, MRR $290k
- Churn del 3% mensual. Equipo de ventas no llega a cuota
- Rotación 25% anual en CS. Tienen procesos formales pero no bajan a acción
- **Tech level:** Alto. Usan herramientas SaaS, esperan integraciones
- **Necesita:** Reducir churn, alinear ventas, escalar CS

## Audit Methodology

Para cada empresa, se usaron TDDOS los skills disponibles:
1. **Cash:** Power of One, CCC, Gross Margin, Revenue/Employee
2. **Strategy:** OPSP, BHAG, Core Customer, Brand Promise, 7 Strata
3. **People:** FACe, Topgrading, Core Values, A-player assessment
4. **Execution:** Rockefeller Habits, Daily Huddle, WWW, Priorities
5. **Dashboards:** Cash board, Strategy board, People board, Execution board
6. **Sessions:** Iniciar sesión, cerrar sesión
7. **Verne:** ask, review-daily, debate, session-perspective

---

## FINDINGS

### 🔴 CRITICAL (6)

| ID | Finding | Evidence | Impact |
|----|---------|----------|--------|
| **C1** | **22/23 dashboards son HTML vacíos** | Solo `power-of-one.html` tiene `DashboardInteractive.init()`. Los otros 22 son `<p>Dashboard interactivo</p>` sin datos, charts, sliders ni conexión API. | Las 3 empresas ven páginas en blanco con placeholder text. No hay números, no hay gráficas, no hay nada actionable. |
| **C2** | **Worksheets existen pero nadie los ve** | Los datos se guardan vía API pero ningún dashboard los carga. El frontend no existe. | Don Roberto: "Guardé mis números pero no veo nada". |
| **C3** | **Clasificación coloquial falla** | "churn" → general (debería execution). "prima" → general (people). "No tenemos maíz" → general (cash). | Las 3 empresas caen a "general" y reciben respuestas genéricas. |
| **C4** | **"trabajo" en cash keywords da falso positivo** | "Mi prima no rinde en el trabajo" → CASH. "trabajo" está en cash keywords por "capital de trabajo". | Don Roberto recibe consejo de cash cuando pregunta de people. |
| **C5** | **Sin aleatorización** | Misma pregunta 3 veces = mismo texto exacto. Sin variación en preguntas de Verne. | Parece robot, no un board member. |
| **C6** | **No hay onboarding ni presentación** | "¿Quién eres?" cae a general. No hay comando "help" descriptivo. | Un usuario nuevo no sabe qué puede hacer. |

### 🟡 MEDIUM (7)

| ID | Finding | Evidence | Impact |
|----|---------|----------|--------|
| **M1** | **Sin adaptación por tipo de empresa** | Verne trata igual a carnicería (8 emp) que a SaaS (28 emp). Mismas preguntas, mismos principios. | Consultoría necesita matices. Carnicería necesita simplicidad radical. |
| **M2** | **ROC no clasifica** | "Return on Cash" → general. Es término clave de Verne. | Usuarios avanzados no encuentran el concepto. |
| **M3** | **board_debate no referencia historial** | El history se pasa pero no se usa para personalizar respuestas. El turno 2 no sabe qué dijo el turno 1. | El debate no profundiza, solo repite el mismo patrón. |
| **M4** | **Context panel JS existe pero ningún dashboard lo usa** | `context-panel.js` puede mostrar entidades del grafo. Ningún HTML lo activa. | Oportunidad perdida de mostrar conocimiento relevante al lado del dashboard. |
| **M5** | **Session close no encuentra sesión activa** | `close_session(None)` devuelve `session_id=None`. Sin manejo de error. | El ciclo sesión no está completo. |
| **M6** | **Sin sugerencias post-dashboard** | Dashboard (cuando funcione) muestra números pero no dice "basado en tus datos, tu prioridad #1 debería ser reducir CCC". | Números sin contexto = "está padre pero no sé qué hacer". |
| **M7** | **Falta comando `escala verne help`** | El CLI solo lista comandos sin ejemplos contextualizados por tipo de empresa. | Usuario nuevo no sabe por dónde empezar. |

### 🟢 MINOR (5)

| ID | Finding | Evidence |
|----|---------|----------|
| **m1** | **Sin variación en frases de cierre** | 4 frases de cierre en `session_perspective` — se repiten rápido |
| **m2** | **Sin logging de uso** | No hay analytics de qué empresas usan qué skills |
| **m3** | **Sin exportación de datos** | No hay PDF/CSV de worksheets ni dashboards |
| **m4** | **Sin integración con herramientas externas** | No hay Slack, email, ni notificaciones |
| **m5** | **Tests no cubren escenarios coloquiales** | 28 tests pero ninguno con lenguaje de carnicería/consultoría/SaaS |

---

## Summary by Company

| Skill | Carnicería | Consultoría | SaaS |
|-------|:----------:|:-----------:|:----:|
| Cash worksheet | ✅ Guardado | ✅ Guardado | ✅ Guardado |
| Strategy worksheet | ✅ Guardado | ✅ Guardado | ✅ Guardado |
| People worksheet | ✅ Guardado | ✅ Guardado | ✅ Guardado |
| Execution worksheet | ✅ Guardado | ✅ Guardado | ✅ Guardado |
| Cash dashboard | ❌ Vacío | ❌ Vacío | ❌ Vacío |
| Strategy dashboard | ❌ Vacío | ❌ Vacío | ❌ Vacío |
| People dashboard | ❌ Vacío | ❌ Vacío | ❌ Vacío |
| Execution dashboard | ❌ Vacío | ❌ Vacío | ❌ Vacío |
| Power of One interactive | ❌ No conectado | ❌ No conectado | ❌ No conectado |
| Verne ask | ⚠️ Vocabulario coloquial falla | ⚠️ Términos técnicos no cubiertos | ⚠️ Churn no clasifica |
| Verne review-daily | ⚠️ Funciona pero genérico | ⚠️ Igual | ⚠️ Igual |
| Verne debate | ⚠️ Sin memoria de historial | ⚠️ Igual | ⚠️ Igual |
| Session flow | ❌ Sin onboarding | ❌ Sin onboarding | ❌ Sin onboarding |
| Session close | ⚠️ No encuentra sesión | ⚠️ No encuentra sesión | ⚠️ No encuentra sesión |

## Done Criteria

- [ ] C1-C6 resueltos
- [ ] M1-M7 resueltos  
- [ ] Auditoría commiteada en E22

## Implementation Plan

> Added by `/rai-epic-plan` — 2026-05-30

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale |
|:-----:|-------|:----:|--------------|-----------|-----------|
| 1 | **S22.1 — Vocabulario coloquial** | S | — | M1 | Quick win alto impacto: arreglar C3, C4, M2 en 1 archivo |
| 2 | **S22.2 — Aleatorización + presentación** | S | — | M1 | Quick win: C5, C6, M7. Verne deja de sonar a robot |
| 3 | **S22.3 — board_debate con memoria** | S | — | M1 | Quick win: M3 + validación. El debate profundiza |
| 4 | **S22.4 — Power of One dashboard vivo** | M | S14 | M2 | **Primer dashboard funcional.** Conectar API data al HTML existente |
| 5 | **S22.5 — Cash dashboards restantes** | M | S22.4 | M2 | CCC, Fundability, Recurring Revenue, Cash Board |
| 6 | **S22.6 — Strategy dashboards** | M | S22.4 | M2 | BMC, Brand Promises, Core Customer, Diff Activities, Sandbox |
| 7 | **S22.7 — People dashboards** | M | S22.4 | M2 | Core Values, DISC, FACe, Hiring Pipeline, Love/Loathe, Team Growth |
| 8 | **S22.8 — Execution dashboards** | M | S22.4 | M2 | Balanced KPIs, Influencers, Meeting Rhythms, Priorities, Rockefeller Habits, Vision Summary, WWW |
| 9 | **S22.9 — Context panel + sugerencias** | S | S22.4 | M2 | M4 + M6. Contexto del grafo al lado + "basado en tus datos..." |
| 10 | **S22.10 — Sesiones + adaptación** | S | — | M3 | M5 + M1. Session close fix + conciencia de tipo de empresa |
| 11 | **S22.11 — Tests coloquiales** | S | S22.1 | M3 | m5. Tests con lenguaje de carnicería, consultoría, SaaS |
| 12 | **S22.12 — Export, logging, pulido** | S | — | M3 | m1-m4: variación, export CSV, logging, integraciones |

### Milestones

| Milestone | Stories | Success Criteria |
|-----------|---------|------------------|
| **M1: Quick Wins** | S22.1, S22.2, S22.3 | Clasificación arreglada. Verne con personalidad. Debate con memoria. |
| **M2: Dashboards Vivos** | S22.4 — S22.9 | 22 dashboards muestran datos reales de worksheets. Context panel activo. Sugerencias post-dashboard. |
| **M3: Sesiones Pulidas** | S22.10 — S22.12 | Sesiones funcionan. Tests coloquiales pasan. Export disponible. |

### Sequencing Strategy

**Risk-first / Quick wins:** Los primeros 3 stories (S22.1-S22.3) son fixes pequeños
en 1-2 archivos cada uno. Se resuelven rápido mientras calentamos para la
carga pesada.

**Walking skeleton dashboard (S22.4):** Power of One es el único dashboard que
tiene el motor interactivo. Primero lo hacemos funcional (conectar API data),
luego replicamos el patrón a los otros 22 dashboards (S22.5-S22.8). Esto
comprueba la arquitectura antes de escalar.

**Dependency-driven:** S22.5-S22.8 dependen de S22.4 (el patrón). S22.9
depende de tener dashboards funcionales. S22.11 depende de S22.1.

### Parallel Work Streams

```
Tiempo →
M1 (Quick Wins):  S22.1 ─► S22.2 ─► S22.3
                                               ↓
M2 (Dashboards):  S22.4 ─┬─► S22.5 ─► S22.6 ─► merge
                         │       └► S22.7 ────┘
                         └► S22.8 ────────────► merge
                                                    ↓
M3 (Polish):                   S22.9 ─► S22.10 ─► S22.11 ─► merge
                                                    ↓
                                         S22.12 ────┘
```

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S22.1 — Vocabulario coloquial | S | Done | ~5m | 1.0 | ✅ C3, C4, M2 — 9 escenarios coloquiales verificados |
| S22.2 — Aleatorización + presentación | S | Done | ~5m | 1.0 | ✅ C5, C6, M7, m1 — 10 frases, shuffle, whoami |
| S22.3 — board_debate con memoria | S | Done | ~3m | 1.0 | ✅ C5 validación, M3 referencia historial |
| S22.4 — Power of One dashboard vivo | M | Done | ~10m | 1.0 | ✅ loadFromServer fix + defaults realistas |
| S22.5 — Cash Engine Humberto | M | Done | ~15m | 1.0 | ✅ Motor 7 palancas, CCC, benchmarks, 9 tests |
| S22.6 — Power of One conectado al backend | M | Done | ~10m | 1.0 | ✅ API + selector empresas demo |
| S22.7 — Power of One idioma humano + Verne | S | Done | ~10m | 1.0 | ✅ Tooltips, Verne, guardado, toggle |
| S22.8 — 22 dashboards (template) | XL | Done | ~15m | 1.0 | ✅ Generador produce todos con tooltips, Verne, guardado |
| S22.9 — Dashboards visual-only + Daily Analyzer | M | Done | ~10m | 1.0 | ✅ Sin inputs. Radar chart. Score Rockefeller. |
| S22.10 — Sesiones + adaptación | S | Pending | — | — | Session close fix + tipo de empresa |
| S22.11 — Tests coloquiales | S | Pending | — | — | Tests con lenguaje de los 3 buyer personas |
| S22.12 — Export, logging, pulido | S | Pending | — | — | Variación frases, CSV, logging |

### Sequencing Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| S22.4-S22.8: 22 dashboards to wire up | H/H | Power of One como template. Script de generación para los 22. No hacerlos a mano. |
| DashboardInteractive.init() API puede no ser compatible con worksheet data model | M/M | Inspeccionar el JS existente primero. Adaptar si es necesario. |
| m2-m4 (logging, export, integraciones) pueden crecer en scope | M/L | Marcar m2-m4 como "nice to have" — no bloquean M3 |

