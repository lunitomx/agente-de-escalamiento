---
epic_id: E84
jira_key: "ESCALA-50"
phase: architecture
created: 2026-09-30
---

# E84 — Diseño: customer journey proactivo y tableros locales que terminan en una decisión

## Hallazgos gemba (8978f79)

Detalle en `capability-map.md` y `evidence/predesign.json`.

| Pieza | Dónde | Uso en E84 |
|---|---|---|
| Tablero de progreso: markdown en inglés con scores 1-5, pulsos, victorias y atención. Le dice al dueño "Run /escala-diagnose" | `coaching/dashboard/__init__.py`, `escala-skills/escala-dashboard/SKILL.md`, 23 tests | Se conserva sin cambios. E84 añade un submódulo a su lado |
| Tablero de evidencia sin score: conocido, no comparable y pendiente | `coaching/evidence/dashboard.py` (`MetricRequirement`, `build_evidence_dashboard`) | Base de "lo que falta se muestra como falta" |
| Facts con periodo, fuente local, confianza y unidad | `coaching/evidence/facts.py` | Fuente de los números de cada tablero |
| Reporte local autocontenido HTML + MD + JSON, escapado y determinista | `escala_server/financial/report.py` (E38) | Patrón del generador |
| Tableros del servidor (`/api/worksheets`) y HTML con Chart.js por CDN | `escala_server/static/dashboards/**`, `escala-agent/skills/escala-dashboard-generado/` | No son portátiles: los primeros necesitan el servidor y los segundos internet |
| `FunnelMetrics` (prospectos, conversaciones, propuestas, ventas, ticket), todos opcionales | `coaching/diagnose/models.py` | Conteos por etapa del journey |
| El diagnóstico sólo acepta evidencia local `fact`, con `assumptions` y `open_questions` | `coaching/diagnose/primary_constraint.py`, `coaching/core/__init__.py:34` | Por aquí entra el journey al diagnóstico |
| El trigger del especialista de strategy ya incluye "journey" | `escala_server/specialist_team.py:63` | El trigger no cambia |
| Rutas: "cliente" → strategy; "pocos compran", "marketing", "dashboard", "gráfica", "indicadores" → welcome; "tablero de mis ventas" → cash | `catalog.yaml` routes; se corrió `route_request` | Hueco de entrada (S84.1, S84.3) |
| Catálogo cerrado en 64 procedimientos y 65 capacidades | `catalog.yaml`, `tests/test_capability_catalog.py:26-27`, `escala_server/capabilities.py:192` | Sube en +1 |
| Contrato de research: acciones por stdin, se guarda sólo con el sí, `DecisionOption` | `coaching/research/` (E83 S83.1) | Forma de los modelos y del cierre en una decisión |
| `JourneyHypothesis` de E71 S71.5 (diseñado, sin código) | `work/epics/e71-market-intelligence-research/design.md` | Se pliega en S84.1 y S84.2 |
| Asesor de tableros de E73 (planeado, sin código) | `work/epics/e73-adaptive-dashboard-advisor/` | Su núcleo se absorbe en S84.3 y S84.4 (decisión propuesta) |
| `.escala/my-company/` ignorado por git; `.escala/agent/memory/` **no** ignorado | `.gitignore:78`, `git check-ignore` | Todo lo nuevo se escribe bajo `my-company/` |

## Respuesta a la incógnita 1: extender, no reemplazar `coaching/dashboard`

El módulo actual es un **resumen de progreso**: scores de madurez, pulsos, victorias y alertas. No define métricas, no dice de dónde sale cada número, no escribe archivos y no termina en una decisión. No compite con lo que pide E84, que es qué medir, por qué, de dónde sale y cómo verlo.

- **Se extiende.** E84 añade `coaching/dashboard/boards/`, un submódulo con su propio `python3 -m coaching.dashboard.boards` y las acciones `recommend`, `render` y `save`. `python3 -m coaching.dashboard` y sus 23 tests no se tocan.
- **No se toca el cálculo de scores.** Es de E80 S80.2.
- **El procedimiento interno `escala-dashboard` gana pasos.** Si el pedido es "cómo voy", sigue mostrando el progreso. Si es "qué debería ver" o "hazme un tablero", pasa por el recomendador y luego por el generador.
- **Hallazgo para E80.** La salida actual está en inglés y muestra comandos (`/escala-diagnose`, `/escala-pulse`), lo que rompe "una sola puerta" y "español llano". E84 no lo corrige porque está en territorio de E80, pero lo registra como pregunta para el dueño. Mientras siga así, el procedimiento no muestra esa salida cruda: la resume en español.

## Cómo E84 evita añadir superficie

- **Catálogo +1:** un solo procedimiento interno nuevo, `escala-strategy-journey` (64 → 65 procedimientos y 65 → 66 capacidades). Cambian las dos aserciones de `tests/test_capability_catalog.py` y el `!= 64` de `escala_server/capabilities.py:192`.
- **Tableros sin procedimiento nuevo:** viven en `escala-dashboard`, que ya está en el catálogo.
- **Cero** comandos públicos, alias, especialistas o capacidades MVP. `capabilities/mvp/catalog.json` no cambia y el trigger de strategy tampoco.
- **Rutas (decisión propuesta):**
  - Strategy suma `marketing` y `prospecto`.
  - Una ruta nueva `dashboard` (`tablero`, `dashboard`, `grafica`, `indicador`) se pone **primera**. Se probó en memoria: con la ruta antes de diagnose, "tablero de mis prioridades" se iba a execution, "de mis clientes" a strategy e "indicadores del equipo" a people. Con la ruta primera, todo pedido de tablero llega al mismo sitio.
- **Sin procesos que se dupliquen:** la primera regla del recomendador es "si ya existe algo que responde tu pregunta, te lo muestro". Eso cubre el tracker (E82), el reporte de caja (E38), el progreso y los reportes de research.
- **Alternativa rechazada: el journey como cuarto modo de `escala-strategy-research`.** Research está hecho para búsquedas web con tres fuentes independientes. El journey vive de evidencia de primera mano (lo que dice el dueño, sus datos y lo que dijeron sus clientes), y mezclarlo debilitaría las dos reglas.

## Experiencia (empresa sintética "Pan Rico", panadería con pedidos por WhatsApp)

1. Dueño: "Mucha gente pregunta por WhatsApp pero pocos compran."
2. ESCALA responde lo que pidió. Como la frase activa un disparador (T1) y nada lo bloquea, añade **una** pregunta: "Para ver dónde se te van, ¿me cuentas cómo llega un cliente hasta que te compra? Son 5 pasos y 5 minutos. Si prefieres, lo vemos después."
3. Si dice "después", ESCALA no vuelve a preguntar en 30 días (N2). Si dice que sí, lo entrevista etapa por etapa (se entera, pregunta, compra, recibe, regresa): qué necesita el cliente ahí, dónde pasa, qué lo frena, cómo lo sabe y cuántos fueron el mes pasado.
4. ESCALA arma el journey:
   - "Preguntan: 120 en septiembre (lo dice tu WhatsApp Business)."
   - "Compran: 18 en septiembre (tu cuaderno)."
   - "Regresan: falta, ¿cuántos de esos 18 volvieron?"
   - "Lo que frena al preguntar es que tardas en contestar. Esto es lo que tú crees: no se lo hemos preguntado a clientes."
   - "Donde más se pierden es entre preguntar y comprar: de 120 a 18 en el mismo mes."
5. Cierra con una decisión. Opción A: "responder en menos de 1 hora durante 14 días y contar de nuevo". Opción B: "todavía no: primero cuento cuántos regresan, para el 15 de octubre". ESCALA recomienda A. El dueño elige y sólo entonces se guarda en `.escala/my-company/journey/`.
6. Si luego pide "un tablero de mis ventas", ESCALA propone **uno o dos** tableros. Cada propuesta dice qué decisión sirve, quién lo mira, cada cuánto, de 3 a 5 métricas con su fuente y si "se puede hoy" o "necesita datos: X". Si el dueño acepta, genera `.escala/my-company/tableros/2026-10-01-ventas.html` más su versión en el chat, y avisa que el archivo "sólo está en tu computadora; no se publica".

## Componentes por historia

### S84.1 — Disparadores y entrevista (`ESCALA-63`, M)

- **`coaching/journey/triggers.py`**, con una función pura `should_ask_journey(signals: JourneySignals) -> AskDecision` (ask, reason, message). Los bloqueos se evalúan **antes** que los disparadores.
- **Preguntar si se cumple alguno de estos:**
  - **T1** Las palabras del dueño caen en el léxico de ventas, marketing o retención: "pocos compran", "no regresan", "se me van", "no vendo", "marketing", "prospectos", "no me llegan clientes". Es una lista cerrada y probada.
  - **T2** La restricción diagnosticada es strategy, o es cash por ventas o precio (no por liquidez ni cobranza).
  - **T3** `FunnelMetrics` tiene algunas etapas con número y otras sin él.
  - **T4** El recomendador de tableros necesita etapas del journey para un tablero de ventas, marketing o retención.
  - **T5** Una decisión de mercado o benchmark de E83 trata de adquisición o canal.
- **No preguntar nunca si se cumple alguno de estos:**
  - **N1** Hay un journey vigente, sin pasar su `review_by`. Si está vencido, se ofrece actualizarlo en lugar de hacer uno nuevo.
  - **N2** El dueño dijo "no" o "después" en los últimos 30 días.
  - **N3** Ya se preguntó en esta conversación: máximo una vez. El módulo no ve la conversación, así que el procedimiento pasa la bandera `asked_this_conversation`.
  - **N4** La restricción es de people o execution y no hay señal de ventas.
  - **N5** Hay otro flujo en curso (research, tracker o cierre). Se pregunta al terminar.
  - **N6** Hay una emergencia de liquidez o de nómina.
- **Memoria de la pregunta:** `.escala/my-company/journey/asks.yaml` guarda la fecha, el resultado (sí/después/no) y el motivo. Así N2 se puede probar.
- **Entrevista:** 5 etapas en español llano, con una pregunta por campo, y "no sé" es una respuesta válida. La salida es un borrador (`JourneyDraft`) que todavía no se guarda.
- **Catálogo:** se crean `escala-skills/escala-strategy-journey/SKILL.md` (`visibility: internal`, owner strategy), la entrada en el catálogo y el cambio de rutas de strategy (`marketing`, `prospecto`). También se agregan casos a la tabla de rutas de `tests/test_capability_catalog.py`.

### S84.2 — Modelo con evidencia, huecos y decisión (`ESCALA-64`, M)

- **`coaching/journey/models.py`** (Pydantic estricto). Cada `JourneyStage` tiene: etapa (una de 5 fijas), necesidad, dónde pasa, fricción, evidencia[], confianza, conteo opcional con periodo y fuente local, y experimento opcional. Son los campos del `JourneyHypothesis` de E71.
- **Origen de la evidencia**, siempre uno de estos cuatro: `dueño_dice`, `dato_con_periodo` (archivo, CRM o fact local), `clientes_dijeron` (de primera mano: el dueño dice cuándo y a cuántos preguntó) o `supuesto`. **Regla de E71:** si no hay evidencia `clientes_dijeron`, el texto dice "esto no se lo hemos preguntado a clientes". Nunca afirma que se entrevistó a nadie.
- **Conteos:** se mapean a `FunnelMetrics` sólo si comparten un mismo periodo. Un conteo que falta se muestra como "falta" y nunca se estima.
- **"Dónde se pierden más":** se calcula sólo con dos etapas **consecutivas** que tengan conteo del **mismo periodo**. Si no se puede, dice "todavía no se puede saber: falta X".
- **Decisión:** reutiliza la forma de `DecisionOption` de research, con 2 o 3 opciones. Una es "trabajar la etapa N con un experimento de 7 a 14 días". Otra es "todavía no", y exige el dato que falta y una fecha. La recomendación tiene que ser una de las opciones.
- **Guardado (`save`):** sólo después del sí del dueño, en `.escala/my-company/journey/AAAA-MM-DD-journey.md` más `journey.yaml`, con `review_by` a 90 días (misma frescura que E83).
- **Costura con el diagnóstico (`to_diagnostic_inputs`):**
  - La decisión elegida entra como `DiagnosticEvidence` `conversation`/`fact` con `source_ref` a la ruta local.
  - Los `supuesto` van a `assumptions` y los faltantes a `open_questions`.
  - `coaching/diagnose/models.py` no cambia.
- **Dónde viven los conteos:** en el archivo del journey bajo `my-company/`, no en `facts.yaml`. Es una decisión propuesta: `.escala/agent/memory/` no está ignorado por git (hallazgo para E79).

### S84.3 — Recomendador de tableros (`ESCALA-65`, M)

- **`coaching/dashboard/boards/recommend.py`** devuelve máximo **2** `BoardProposal`. Cada una trae:
  - la decisión o pregunta que sirve,
  - quién lo mira,
  - cada cuánto,
  - de 3 a 5 métricas como `MetricRequirement` (definición, fuente y periodo),
  - factibilidad: `se_puede_hoy`, `necesita_datos` (con la lista) o `no_ahora`.
- **Reglas, en orden:**
  1. **Sin redundancia.** Si un artefacto existente responde la pregunta (tracker, reporte de caja, progreso o research), lo señala y no propone nada nuevo.
  2. **Se parte de una decisión.** Si el pedido no trae decisión ("muéstrame un dashboard"), se hace **una** pregunta: "¿qué quieres decidir con esto?".
  3. **Catálogo corto de patrones por área:**
     - ventas y journey: conversión entre etapas y clientes que regresan;
     - caja: el reporte existente;
     - equipo: carga y avance, **nunca un ranking individual**;
     - ejecución: el tracker.
  4. **El estado de cada métrica** sale de `build_evidence_dashboard`: conocido, no comparable o pendiente.
  5. **Si hacen falta etapas del journey**, se consulta `should_ask_journey` (T4).
- **Memoria:** aceptar, posponer o rechazar se guarda en `.escala/my-company/tableros/index.yaml`. Un tablero rechazado o pospuesto no se vuelve a proponer en 30 días (el mismo N2 de S84.1).
- **Cierre:** termina en la decisión del dueño de construirlo, esperar o no hacerlo.
- **Ruta nueva `dashboard`, primera en la lista,** hacia `escala-dashboard`. Se agregan casos a la tabla de rutas: "tablero de mis ventas", "muéstrame un dashboard", "qué indicadores debo ver" y "quiero cobrar más rápido" (este último debe seguir en cash).

### S84.4 — Generador de tablero local (`ESCALA-66`, M)

- **Respuesta a la incógnita 2 (decisión propuesta):** un **solo HTML autocontenido más su gemelo Markdown**, con el mismo contenido. `coaching/dashboard/boards/render.py`:
  - CSS en línea y barras en SVG en línea. **Sin JavaScript**, sin CDN, sin fuentes externas, sin `url(` ni `@import`.
  - Todo el texto pasa por `html.escape`. La salida es determinista (mismos datos, mismos bytes), con el patrón de `escala_server/financial/report.py`.
- **Dónde y cuándo se guarda:** `save` escribe `.escala/my-company/tableros/AAAA-MM-DD-<slug>.html` y `.md`, de forma atómica. Sólo lo hace con la propuesta aceptada y con factibilidad distinta de `no_ahora`.
- **Contenido fijo del tablero:**
  - Encabezado: "Sólo en tu computadora; no se publica."
  - Cada número muestra su fuente y su periodo.
  - Cada faltante dice "Falta: <dato>, cómo conseguirlo".
  - Pie: la decisión a la que sirve el tablero.
- **Sin ningún número no se genera tablero.** Se muestra la lista de datos que conseguir, que es la decisión "todavía no".
- **Reglas del procedimiento:**
  - Nunca publicar con artifacts, canvas, enlaces compartidos ni nada parecido.
  - El Markdown se muestra en el chat.
  - Si el cliente no puede correr Python o escribir archivos, se muestra sólo el Markdown y se dice que no se guardó.
- **Tests:**
  - la salida no contiene `http`, `<script`, `@import` ni `url(`;
  - los faltantes se muestran como faltantes;
  - el texto va escapado;
  - la salida es determinista;
  - el HTML y el MD dicen lo mismo;
  - no se genera tablero sin números.
- **Matriz por plataforma**, con un comando de reproducción por fila. Se llena en S84.4 y lo que no se probó queda "no verificado".

| Cliente | Correr el procedimiento (python por shell) | Escribir en `.escala/my-company/` | Abrir el HTML local | Estado |
|---|---|---|---|---|
| Claude Code | Así está diseñado el repo (E67) | Así está diseñado | Depende del sistema del dueño | no verificado en una instalación de dueño |
| Codex | Así está diseñado (adaptadores E67) | Así está diseñado | Depende del sistema del dueño | no verificado |
| claude.ai / Desktop | Desconocido | Desconocido | Desconocido | no verificado |
| ChatGPT Work | Desconocido | Desconocido | Desconocido | no verificado hasta E85 |

El **piso garantizado** es el Markdown en el chat. El HTML es una mejora cuando el cliente puede escribir archivos. No se afirma nada por el nombre de la plataforma.

## Contratos clave

```python
class JourneySignals(BaseModel):  # entrada de should_ask_journey
    owner_text: str
    constraint_area: Literal["cash","people","strategy","execution"] | None
    cash_topic: Literal["ventas","precio","liquidez","cobranza"] | None
    funnel_known: list[str]; funnel_missing: list[str]
    board_needs_stages: bool; research_topic_acquisition: bool
    journey_review_by: date | None; last_declined_on: date | None
    asked_this_conversation: bool; other_flow_active: bool; cash_emergency: bool
    today: date

class AskDecision(BaseModel):
    ask: bool; reason: str   # código T1..T5 / N1..N6
    message: str | None      # español llano, una sola pregunta

class BoardProposal(BaseModel):
    decision: str; audience: str; cadence: str
    metrics: list[MetricRequirement]           # 3-5
    feasibility: Literal["se_puede_hoy","necesita_datos","no_ahora"]
    missing: list[str]; points_to_existing: str | None   # ruta local
```

## Incógnitas: decisiones propuestas (pendientes de confirmar por el dueño)

| # | Incógnita | Decisión propuesta — pendiente de confirmar por el dueño |
|---|---|---|
| U1 | Extender o reemplazar `coaching/dashboard` | Extender con el submódulo `boards/`; el progreso actual queda intacto |
| U2 | Formato local común | Un HTML autocontenido (sin JS ni red) más su gemelo Markdown; el Markdown en el chat es el piso |
| U3 | Qué hacer con E73 (ESCALA-37) | E84 absorbe su núcleo (propuestas, factibilidad, memoria de decisiones, formato local), igual que E83 absorbió a E71; el dueño aplica la disposición en Jira |
| U4 | Rutas nuevas | Strategy + `marketing`, `prospecto`; ruta `dashboard` primera |
| U5 | Ventana para no insistir | 30 días tras "no" o "después"; una pregunta por conversación |
| U6 | Dónde viven los conteos del journey | En `.escala/my-company/journey/`, no en `facts.yaml` |
| U7 | Idioma y comandos del tablero de progreso | Lo corrige E80; mientras tanto el procedimiento lo resume en español |

## Otras incógnitas

- Si `.escala/agent/memory/` debería estar ignorado por git (facts y perfil viven ahí). Es de E79 y se registra aquí como hallazgo.
- Si los dueños abren de verdad el HTML o se quedan con el chat. Se observa en el primer uso real, no se asume.
- E75 nombra a E71/E73 como destinos del hand-off; tras la absorción serían E83/E84. Es un ajuste de texto en E75 que E84 no hace.

## Revisión adversarial

Autorrevisión en `design.redteam.json`. Cambios que dejó: N3 se vuelve una bandera de entrada; los conteos llevan periodo propio porque `FunnelMetrics` no tiene periodo; no se genera tablero sin números; la ruta `dashboard` señala el reporte de caja cuando el pedido es de caja; y la matriz por plataforma queda como no verificada.

### Machine
```yaml
modules_affected:
  - path: coaching/journey/
    change: create
  - path: coaching/journey/tests/
    change: create
  - path: coaching/dashboard/boards/
    change: create
  - path: coaching/dashboard/boards/tests/
    change: create
  - path: escala-skills/escala-strategy-journey/SKILL.md
    change: create
  - path: escala-skills/escala-dashboard/SKILL.md
    change: modify
  - path: escala-skills/catalog.yaml
    change: modify
  - path: escala_server/capabilities.py
    change: modify
  - path: tests/test_capability_catalog.py
    change: modify
decisions:
  - id: D1
    choice: "Extender coaching/dashboard con el submódulo boards/ (recommend, render, save); el progreso actual y sus 23 tests quedan intactos"
    rationale: "El módulo actual resume progreso; no compite con 'qué medir y por qué'"
    constraint: "No tocar el cálculo de scores (E80 S80.2)"
  - id: D2
    choice: "Un solo procedimiento interno nuevo escala-strategy-journey; los tableros viven en escala-dashboard (ya existe)"
    rationale: "Una sola puerta; catálogo +1"
    constraint: "Ningún comando, alias, especialista ni capacidad MVP nueva; trigger de strategy sin cambio"
  - id: D3
    choice: "Disparadores T1-T5 y bloqueos N1-N6 en una función pura; los bloqueos se evalúan primero (decisión propuesta)"
    rationale: "Proactivo sin insistir, y comprobable con tests"
    constraint: "Máximo una pregunta por conversación; 30 días de silencio tras 'no' o 'después'"
  - id: D4
    choice: "Journey de 5 etapas fijas; cada evidencia con origen dueño_dice / dato_con_periodo / clientes_dijeron / supuesto"
    rationale: "Regla de E71: separar primera mano de inferencia"
    constraint: "Nunca afirmar que se entrevistó a clientes sin evidencia clientes_dijeron"
  - id: D5
    choice: "'Dónde se pierden más' sólo con dos etapas consecutivas contadas en el mismo periodo"
    rationale: "Sin números inventados"
    constraint: "Un conteo faltante se muestra como 'falta', nunca se estima"
  - id: D6
    choice: "Journey, recomendación y tablero terminan en 2-3 opciones con una recomendación, incluida 'todavía no' con dato y fecha"
    rationale: "Cada módulo termina en una decisión"
    constraint: "Nada se guarda sin el sí del dueño"
  - id: D7
    choice: "El journey entra al diagnóstico como evidencia conversation/fact con la ruta local; supuestos a assumptions, faltantes a open_questions"
    rationale: "Mismo patrón que E83 S83.5; no cambia el contrato de diagnóstico"
    constraint: "coaching/diagnose/models.py no cambia; ninguna URL"
  - id: D8
    choice: "Recomendador: máximo 2 propuestas, primero apuntar a lo que ya existe, métricas como MetricRequirement con estado de build_evidence_dashboard (decisión propuesta: absorbe E73)"
    rationale: "Reutilizar el contrato de evidencia y no duplicar tracker ni reporte de caja"
    constraint: "Equipo sin ranking individual"
  - id: D9
    choice: "Formato: HTML autocontenido sin JS ni red más un gemelo Markdown; el Markdown en el chat es el piso (decisión propuesta)"
    rationale: "Lo único que no depende de servidor, internet ni capacidades de cada cliente"
    constraint: "Nunca publicar; sin http, <script, @import ni url( en la salida"
  - id: D10
    choice: "Rutas: strategy + marketing, prospecto; ruta dashboard primera (decisión propuesta)"
    rationale: "Probado en memoria: en otra posición los pedidos de tablero se reparten entre áreas"
    constraint: "'Quiero cobrar más rápido' sigue en cash; los casos actuales de rutas no cambian"
constraints:
  - "Todo lo que escribe E84 va bajo .escala/my-company/ (ignorado por git), nunca en .escala/agent/memory/"
  - "Tests sólo con fixtures sintéticos; nada de ~/Downloads, .escala/ reales ni .scaleup/"
  - "Ninguna afirmación de plataforma sin la matriz verificada de S84.4; ChatGPT Work no verificado hasta E85"
  - "Texto al usuario en español llano, sin nombres de procedimientos ni comandos"
  - "Catálogo: dos aserciones cambian (64 -> 65, 65 -> 66) y el chequeo de capabilities.py"
  - "Tipos completos, modelos Pydantic, pyright strict"
```
