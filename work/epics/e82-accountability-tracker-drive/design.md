---
epic_id: E82
jira_key: "ESCALA-48"
phase: architecture
created: 2026-09-30
---

# E82 — Diseño: tracker de accountability guiado

## Hallazgos gemba (lo que ya existe)

| Pieza | Dónde | Uso en E82 |
|---|---|---|
| Lectura del workbook con fórmulas resueltas (Claude Drive) | S82.1 | Único camino de lectura verificado |
| Sin escritura de celdas en el conector de Claude | S82.1 | S82.4 entrega filas para pegar; escritura directa sólo tras S82.6 |
| `parse_connector_text`, `parse_sheet`, `TrackerSheet`/`TrackerItem` | `coaching/tracker/` | Base de S82.3–S82.5; no se reescribe |
| Nombre de participante puede ser un placeholder de fórmula ("Name 6") | retro S82.2 | S82.3 nunca decide por la celda |
| Puerta pública única `escala` + especialista privado de execution | `escala-skills/escala/SKILL.md`, `adapters/*/agents/escala-execution.*` | El flujo entra por aquí; el usuario no aprende comandos |
| Catálogo cerrado de procedimientos (baseline 62) | `escala-skills/catalog.yaml`, `tests/test_capability_catalog.py` | Un procedimiento interno nuevo sube la baseline a 63 |
| `quarterly_plan` (critical_number, priorities, theme) | `coaching/strategy_opsp/engine.py`, `.escala/my-company/opsp.yaml` | Fuente de las filas propuestas en S82.4 |
| No hay lector `.xlsx` ni dependencia `openpyxl` | `coaching/tracker/`, `pyproject.toml` | No se añade; ver D5 |

## Experiencia (lo que ve el empresario)

Todo en español llano, un paso por mensaje, y ESCALA propone el siguiente paso.

1. El usuario menciona su tracker, su grupo o "mi hoja", o ESCALA termina de definir prioridades trimestrales y ofrece: "¿Las pasamos a tu hoja del grupo?".
2. "¿Cómo te llamas?" (sólo el nombre; el negocio se pregunta únicamente si dos pestañas empatan).
3. Si no hay conector de Drive: "Para leer tu hoja, conecta Google Drive en tu Claude (Configuración → Conectores). Ojo: al conectarlo, el asistente puede ver todo el archivo compartido del grupo; ESCALA sólo usa tu pestaña. Si prefieres no conectarlo, abre tu pestaña, selecciónala toda, cópiala y pégala aquí." No se prometen pasos para ChatGPT (E85). La línea de aviso es obligatoria (decisión del dueño, AR-E82).
4. ESCALA busca el archivo y muestra **sólo nombres de pestaña**, con la que coincide con el nombre del usuario como candidata: "Veo una pestaña que se llama **Eduardo**. ¿Es la tuya?". Si ninguna coincide, lista los nombres de pestaña y pregunta cuál es. Sólo después del sí lee las celdas de esa pestaña; si la celda de nombre es un placeholder o está vacía, lo dice entonces: "Tu pestaña dice 'Name 6' en vez de tu nombre; puedo trabajar igual, y conviene avisar al grupo para que llene START HERE". Nunca se cita el contenido de una pestaña antes de confirmarla.
5. Con el sí, ESCALA recuerda la elección para la próxima vez (pregunta de nuevo si el archivo o la pestaña cambian).
6. S82.4: "Te propongo estas 3 filas para tus compromisos de octubre" → tabla + bloque listo para pegar + dónde pegarlo ("debajo de la última fila de Monthly Commitments").
7. S82.5: "Antes de tu reunión: 2 compromisos vencidos, 1 terminado que puedes pasar a Done." → propuesta concreta, nada se mueve sin su sí.

## Componentes objetivo

### S82.3 — identidad y hoja propia (`coaching/tracker/identity.py`)

- `is_placeholder_name(name: str | None) -> bool` — vacío, `Name \d+`, `Participant Name`, `#REF!`/errores de fórmula.
- `rank_candidates(tab_names: list[str], name: str, business: str | None = None) -> list[SheetCandidate]` — puntúa **sólo por el nombre de pestaña** (normalizado: acentos, mayúsculas) contra el nombre del usuario; `business` sólo desempata; excluye `START HERE`; marca `needs_confirmation=True` siempre. Nunca devuelve una elección final. No recibe `TrackerSheet`: las celdas de las otras pestañas no se parsean. Tras elegir, de `parse_connector_text` se conserva sólo la cuadrícula de `tab_name`; las demás se descartan antes de cualquier `parse_sheet`.
- `is_placeholder_name` se aplica a la pestaña **ya confirmada** (para avisar), no para elegir.
- `TrackerLink` (Pydantic): `file_title`, `file_id | None`, `tab_name`, `participant_confirmed`, `confirmed_at`. Guardado en `.escala/my-company/tracker.yaml` sólo tras la confirmación, por el procedimiento (no por el agente especialista, cuyo contrato dice "do not persist state"). Guarda la referencia, no el contenido. **Hoy `.escala/my-company/` no está en `.gitignore` y partes de `.escala/` sí están versionadas** (`git check-ignore` falla): S82.3 añade `.escala/my-company/` a `.gitignore` antes de escribir el primer archivo.
- `parse_pasted_tab(text: str) -> Grid` — separa por `\t` y saltos de línea (formato que Sheets deja al copiar) → `parse_sheet`. Es el camino sin conector.

### S82.6 — spike de escritura (sin código de producto)

Límite de tiempo: 1 día. Sólo sobre una copia sintética, que después se manda a la papelera. Candidatos: (a) conector de Drive de ChatGPT Work, (b) un MCP de Google Sheets con escritura por celda en Claude Desktop/Code, (c) el mismo MCP en Codex.
Criterios GO (todos): el empresario lo instala sin terminal en ≤ 5 pasos (aplica a claude.ai / Claude Desktop, que es donde está el empresario; Claude Code y Codex son superficies del dueño y no cuentan para este criterio); el permiso se puede limitar a ese archivo o, como mínimo, es auditable; escribe un rango de una pestaña concreta sin tocar fórmulas ni otras pestañas; el cambio se puede revertir (historial de versiones de Sheets).
Salida: tabla verificada (igual que S82.1) + GO/NO-GO por superficie + comando para reproducir.

### S82.4 — proponer filas (`coaching/tracker/proposal.py`)

- `propose_rows(sheet: TrackerSheet, plan: QuarterlyPlanInput, month: str) -> RowProposal` — `QuarterlyPlanInput` es un modelo Pydantic **nuevo** construido desde la sección `quarterly_plan` del estado OPSP (hoy un `dict[str, Any]` en `coaching/strategy_opsp/engine.py`, no un tipo); mapea las prioridades de `quarterly_plan` a filas `Focus Area · Priority · KPI · Due Date`; usa las etiquetas de área que la hoja ya usa (variación 5 de S82.2), se salta las que ya están escritas (comparación normalizada) y no propone un Critical Number si la hoja ya tiene uno distinto: lo señala y pregunta.
- `to_paste_block(rows) -> str` — TSV en el orden de columnas de la hoja, para pegar en Sheets. Más una tabla legible.
- Escritura directa: sólo si S82.6 da GO en esa superficie, detrás de una confirmación explícita de filas + pestaña, y sólo sobre el `tab_name` de `TrackerLink`. Si da NO-GO, esta rama no se construye.

### S82.5 — mantenimiento previo a la reunión (`coaching/tracker/maintenance.py`)

- `review_before_meeting(sheet: TrackerSheet, today: date) -> MeetingPrep` — vencidos (fecha < hoy y estado sin terminar), terminados que siguen en compromisos (proponer moverlos a `Done`), filas sin KPI o sin fecha.
- `parse_due(text: str | None) -> date | None` — ISO, `dd/mm/yyyy` y nombres de mes en español/inglés. Sin rama `mm/dd`: como el formato real no está catalogado (U4), cualquier fecha ambigua queda como "fecha por confirmar"; no se adivina. Se amplía sólo si un fixture real (sintetizado) lo exige.
- Estado terminado: vocabulario cerrado (`done`, `hecho`, `terminado`, `completado`, `✅`, `100%`); lo demás es "sin terminar".
- Salida: resumen en español + bloque para pegar en `Done`. Sin escrituras en el MVP.

### Superficie conversacional (sin comandos nuevos)

- Un procedimiento interno `escala-execution-tracker` (`escala-skills/escala-execution-tracker/SKILL.md`), `visibility: internal`, `owner: execution`, al que se llega sólo desde `escala` vía el especialista de execution. El usuario nunca lo ve ni lo nombra.
- Ruta real: `escala/SKILL.md` enruta por `capabilities/mvp/catalog.json` (seis capacidades MVP; `capability.set-quarterly-priority` → `procedure.set-quarterly-priority`, perfil `specialist.execution.v1`). El tracker **no es una capacidad MVP nueva**: es un sub-procedimiento alcanzado desde ese procedimiento (paso final de `escala-execution-prioridad` / `escala-execution-priorities`) o cuando el especialista de execution reconoce `tracker de accountability / hoja del grupo`. `capabilities/mvp/catalog.json` no cambia.
- Se añade `tracker de accountability / hoja del grupo` al `trigger` del especialista de execution en `adapters/specialists/contract.json` y en `adapters/claude/agents/escala-execution.md` / `adapters/codex/agents/escala-execution.toml`, y un paso final en `escala-execution-prioridad` / `escala-execution-priorities` que ofrece llevarlo al tracker.
- Entrada del catálogo cerrado + en `tests/test_capability_catalog.py` **dos** aserciones cambian: baseline `canonical_procedures` 62 → 63 y `len(catalog.capabilities)` 63 → 64 (cambio de gobierno; decisión del dueño ya tomada).

## Contratos clave

- Entrada de lectura: texto del conector (`parse_connector_text`) o pestaña pegada (`parse_pasted_tab`). Ambos terminan en `TrackerSheet`.
- De un workbook sólo se procesa y se retiene la pestaña confirmada. De las demás se usa el nombre de pestaña (para elegir) y nada más: no se resumen, no se citan, no se guardan.
- Todo lo que se persiste va a `.escala/my-company/` (local). Hoy esa ruta **no** está ignorada por git; S82.3 la añade a `.gitignore` (ver S82.3). Tests: sólo fixtures sintéticos.
- Privacidad del flujo: antes de la confirmación sólo circulan nombres de pestaña (ya visibles al usuario en Drive). Ningún mensaje de ESCALA, journal ni archivo local cita celdas de una pestaña no confirmada.

## Incógnitas abiertas (no se afirman)

- U1: si ChatGPT Work lee o escribe Sheets, y si ESCALA corre ahí (E85). Hasta cerrarla, la guía de conexión sólo nombra Claude.
- U2: Codex no tiene conector de Drive verificado; en Codex el camino es la pestaña pegada salvo que S82.6 valide un MCP.
- U3: el conector lee el workbook entero, así que los datos de otros participantes entran en el contexto del modelo aunque ESCALA no los use. Hay que decírselo al usuario en una línea al conectar. No se puede evitar con el conector actual.
- U4: el formato de las fechas en hojas reales no está catalogado (S82.2 no lo midió); `parse_due` es conservador a propósito.
- U5: si al pegar un TSV en Sheets se rompen validaciones o formatos condicionales de la plantilla. Se verifica en S82.4 con la copia sintética.
- U6: cadencia de la reunión del grupo (¿mensual?). S82.5 recibe `today` y no asume la cadencia.

### Machine
```yaml
modules_affected:
  - path: coaching/tracker/identity.py
    change: create
  - path: coaching/tracker/proposal.py
    change: create
  - path: coaching/tracker/maintenance.py
    change: create
  - path: coaching/tracker/tests/
    change: modify
  - path: escala-skills/escala-execution-tracker/SKILL.md
    change: create
  - path: escala-skills/catalog.yaml
    change: modify
  - path: tests/test_capability_catalog.py
    change: modify
  - path: adapters/specialists/contract.json
    change: modify
  - path: adapters/claude/agents/escala-execution.md
    change: modify
  - path: adapters/codex/agents/escala-execution.toml
    change: modify
  - path: .gitignore
    change: modify
  - path: escala-skills/escala-execution-prioridad/SKILL.md
    change: modify
  - path: escala-skills/escala-execution-priorities/SKILL.md
    change: modify
decisions:
  - id: D1
    choice: "Una sola puerta: se entra por `escala` y el especialista de execution llega a un procedimiento interno escala-execution-tracker"
    rationale: "El usuario no aprende comandos; las reglas del tracker viven en un solo sitio"
    constraint: "Ningún comando ni alias público nuevo"
  - id: D2
    choice: "La hoja propia se elige por nombre de pestaña (rank_candidates) más la confirmación explícita del usuario; la elección se persiste en TrackerLink"
    rationale: "La celda de nombre puede ser un placeholder de fórmula ('Name 6'); leer celdas de otras pestañas para elegir viola D4"
    constraint: "Nunca elegir una pestaña sin el sí del usuario; nunca citar celdas de una pestaña no confirmada; nunca usar START HERE como hoja de participante"
  - id: D3
    choice: "El MVP de S82.4 entrega un bloque TSV para pegar más una tabla legible; la escritura directa sólo si S82.6 da GO por superficie"
    rationale: "El conector verificado no escribe celdas (S82.1)"
    constraint: "No crear archivos nuevos ni reemplazar el workbook compartido"
  - id: D4
    choice: "Se procesa y se retiene sólo la pestaña confirmada; de las otras, sólo el nombre de pestaña"
    rationale: "El archivo compartido contiene datos de todo el grupo"
    constraint: "No leer para usar, citar, resumir ni escribir hojas de otros participantes"
  - id: D5
    choice: "Sin lector .xlsx ni dependencia nueva; el camino sin conector es pegar la pestaña (TSV)"
    rationale: "Simple primero; pegar funciona en cualquier cliente"
    constraint: "No añadir openpyxl ni un conector propio a Google"
  - id: D6
    choice: "S82.5 sólo propone (vencidos, pasar a Done, faltantes); fechas ambiguas quedan 'por confirmar'"
    rationale: "No adivinar datos del empresario"
    constraint: "No mover ni marcar filas sin confirmación"
constraints:
  - "S82.6 se completa antes de S82.4"
  - "Tests sólo con fixtures sintéticos; nada de ~/Downloads, .escala/ ni .scaleup/ en el repo"
  - "Estado persistido sólo en .escala/my-company/ (local); S82.3 añade esa ruta a .gitignore antes del primer archivo"
  - "Aviso de una línea al conectar Drive: el asistente ve todo el archivo compartido; ESCALA sólo usa tu pestaña"
  - "El tracker no añade capacidad a capabilities/mvp/catalog.json; se alcanza desde procedure.set-quarterly-priority"
  - "Guía de conexión: sólo Claude verificado; no afirmar que ChatGPT Work funcione (E85)"
  - "Texto al usuario en español llano, sin jerga interna ni nombres de skills"
  - "Tipos completos, modelos Pydantic, pyright strict"
```
