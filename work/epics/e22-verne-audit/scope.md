# Epic Scope: E22 — Full System Audit (3 Empresas × Todos los Skills)

**Status:** Draft
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

- [ ] C1-C6 creados como stories y priorizados
- [ ] M1-M7 creados como stories
- [ ] Auditoría commiteada en E22
