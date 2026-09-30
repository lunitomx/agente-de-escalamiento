---
epic_id: E83
jira_key: "ESCALA-49"
phase: architecture
created: 2026-09-30
---

# E83 — Diseño: investigación de negocio que termina en una decisión

## Hallazgos gemba (lo que ya existe)

Detalle y evidencia en `capability-map.md` y `evidence/predesign.json` (sobre `6b13dd2`).

| Pieza | Dónde | Uso en E83 |
|---|---|---|
| Puerta pública única `escala`; catálogo cerrado (63 procedimientos, 64 capacidades) | `escala-skills/escala/SKILL.md`, `escala-skills/catalog.yaml`, `tests/test_capability_catalog.py:26-27` | Un solo procedimiento interno nuevo: 63 → 64 y 64 → 65 |
| Rutas por palabra clave: Strategy sólo con `estrategia`, `opsp`, `cliente`, `competencia`, `rumbo` | `catalog.yaml` `routes`, `escala_server/capabilities.py:199` | Hoy "¿cómo está mi mercado?", "¿cómo cobran mis competidores?" y "¿qué tendencias vienen?" caen en welcome (probado con `route_request`). S83.1 añade palabras |
| Especialista privado de strategy: "never present market claims without source and date"; "mark external claims as unverified" | `adapters/specialists/contract.json`, `escala_server/specialist_team.py`, `adapters/*/agents/escala-strategy.*` | Es quien pide la investigación. No se crea un quinto especialista (el test lo rechaza: `tests/test_specialist_team.py:96-98`) |
| SWT canónico, construido sólo con datos internos de sesiones | `escala-skills/escala-strategy-swt/SKILL.md` | El modo 3 le da evidencia externa; no se crea un segundo SWT |
| Evidencia y facts con procedencia; toda fuente debe ser local (sin URL) | `coaching/evidence/models.py`, `coaching/evidence/facts.py`, `coaching/core/__init__.py:34` | Las URLs viven sólo dentro del reporte local; el diagnóstico apunta al reporte, nunca a una URL |
| Diagnóstico: evidencia de evaluación sólo `answer_status="fact"` de fuentes narrativas (`conversation`, `user_file`, `crm_export`, `profile`, `opsp`); listas `assumptions` y `open_questions` | `coaching/diagnose/models.py`, `coaching/diagnose/primary_constraint.py:60-103` | Lo externo entra como supuesto con fuente y fecha; sólo la decisión confirmada por el dueño entra como hecho |
| E75: el diagnóstico propone como máximo dos rutas profundas, el usuario elige; incluye "research/market" | `work/epics/e75-.../design.md` | La investigación es una de esas rutas; el orden de módulos no es fijo |
| E71 (ESCALA-35): contrato de research, TAM/SAM/SOM, competidores, journey. `planned`, sin código | `work/epics/e71-market-intelligence-research/` | Se absorbe en E83 salvo el journey (va a E84). Ver D8 |
| `.escala/my-company/` ignorado por git | `.gitignore:78` (S82.3) | Carpeta de los reportes |
| Patrón de procedimiento interno + módulo Python por JSON en stdin | `escala-skills/escala-execution-tracker/SKILL.md`, `coaching/tracker/` | Se copia la forma |

## Cómo E83 evita añadir superficie

- **Cero comandos públicos, cero alias, cero especialistas nuevos.** El empresario sigue hablando con `escala`.
- **Un solo procedimiento interno** `escala-strategy-research` con **tres modos** (`benchmark`, `mercado`, `fortalezas-tendencias`), no tres procedimientos ni tres comandos. El catálogo sube en uno.
- **El modo 3 no produce su propio documento**: entrega la parte externa (posición frente al mercado y tendencias) a `escala-strategy-swt`, que sigue siendo el único SWT.
- **`capabilities/mvp/catalog.json` no cambia**: la investigación es un sub-procedimiento que se alcanza desde el especialista de strategy o como ruta propuesta por el diagnóstico (E75), igual que el tracker de E82 se alcanza desde las prioridades.
- **El diagnóstico no cambia de contrato**: recibe la decisión confirmada y los supuestos por los campos que ya tiene.
- Lo único que se toca fuera de lo nuevo: palabras clave de la ruta de Strategy, el `trigger` del especialista de strategy (añadir "benchmark o tendencias") y un paso final en `escala-strategy-swt`.

## Experiencia (lo que ve el empresario)

Español llano, un paso por mensaje, ESCALA propone. Nunca aparecen las palabras "módulo", "triangulación", "TAM" ni el nombre del procedimiento.

1. **Entrada.** O el empresario pregunta ("¿cuánto cobran los demás?", "¿cómo está mi mercado?", "¿qué viene para mi sector?"), o ESCALA lo propone al terminar el diagnóstico: "Tu freno parece ser el precio. Antes de decidir, ¿vemos cómo cobran negocios parecidos al tuyo? Son unos minutos."
2. **Encuadre y permiso en un solo mensaje.** "Quieres decidir si subes tus precios. Voy a buscar: *precios de [servicio] en [ciudad] 2026*, *[competidor público] tarifas*, *[sector] [país] márgenes*. No llevo tu nombre ni tus cifras. ¿Va, o cambio algo?" Un sí confirma la pregunta, la decisión que informa y las búsquedas.
3. **Sin búsqueda web en ese asistente.** "Aquí no puedo buscar en internet. Si me pasas dos o tres cosas (el link de un competidor, una cotización que te llegó, lo que te dicen tus clientes), lo hago con eso y te digo hasta dónde llega." Nunca se rellena con lo que el modelo "recuerda".
4. **Resultado corto.** Máximo tres hallazgos. Cada uno dice qué tan seguro es en palabras (**confirmado**: tres fuentes independientes con fecha; **por confirmar**: menos), de dónde sale y de cuándo es. Siempre: "lo que dice lo contrario" y "lo que no encontré".
5. **Termina en una decisión.** "Con esto tus opciones son: A) subir 8% en enero, B) mantener y cambiar el paquete, C) no decidir todavía y conseguir antes [dato concreto] para el [fecha]. Te recomiendo A porque… ¿Cuál tomas?" "No decidir todavía" es válido sólo con el dato que falta y una fecha.
6. **Queda guardado.** Con el sí, el reporte se guarda en su carpeta y la decisión alimenta el siguiente diagnóstico: "La próxima vez que veamos tu empresa, parto de esta decisión."

## Componentes objetivo

### S83.1 — contrato del orquestador (`coaching/research/`)

Modelos Pydantic (nombres tomados del boceto de E71 para no abrir otra taxonomía):

- `ResearchFrame`: `concern` (palabras del dueño), `question`, `decision_informed`, `mode: Literal["benchmark", "mercado", "fortalezas-tendencias"]`, `segment`, `geography`, `offer_category`, `horizon`, `queries: list[str]`, `search_mode: Literal["web", "sin_busqueda"]`, `confirmed: bool`.
- `SourceRecord`: `source_id`, `origin: Literal["web", "dueño", "archivo_empresa"]`, `title`, `publisher`, `url: str | None`, `published_on: date | None`, `consulted_on: date`, `excerpt` (≤ 300 caracteres). No existe un origen "conocimiento del modelo".
- `ResearchClaim`: `text`, `kind: Literal["dato", "supuesto", "inferencia"]`, `supporting: list[source_id]`, `contrary: list[source_id]`, `status: Literal["confirmado", "por_confirmar"]`, `confidence: Literal["alta", "media", "baja"]`.
- `DecisionOption` y `ResearchReport`: encuadre, fuentes, afirmaciones, lo contrario, lo no encontrado, límites, 2-3 opciones, recomendación, `chosen: DecisionOption | None`, `review_by: date`.

Reglas (`engine.py`, deterministas y probadas):

- `grade_claim`: `confirmado` sólo con ≥ 3 fuentes **independientes** (distinto `publisher`) **con fecha** dentro de la ventana de frescura; si no, `por_confirmar`. Una fuente sin fecha no cuenta para las tres. Una afirmación con `contrary` no vacío baja a `media` como máximo y se muestra.
- `supuesto` e `inferencia` nunca se presentan como `dato`.
- `check_queries(frame, blocked_terms)`: las búsquedas se arman sólo con campos del encuadre confirmado; se rechaza cualquier búsqueda que contenga el nombre de la empresa, del dueño o de personas, o cifras de sus facts. **Test de privacidad obligatorio**: empresa sintética con marcadores únicos en nombre, personas y cifras; ninguna búsqueda generada los contiene.
- Sin búsqueda web (`search_mode="sin_busqueda"`): se aceptan sólo fuentes `dueño` o `archivo_empresa`; el reporte abre con el límite ("En este asistente no hubo búsqueda en internet; usé N fuentes que tú diste") y dice qué fuente subiría cada `por_confirmar`.
- Frescura: `review_by = consulted_on + 90 días` (decisión propuesta D6).

Salida (`report.py`): `.escala/my-company/research/AAAA-MM-DD-<modo>.md` (legible) más una entrada en `.escala/my-company/research/index.yaml` (referencia, modo, decisión, `review_by`). Lo escribe el módulo, no el especialista (su contrato dice "do not persist state"), y sólo tras el sí del paso 5.

Entrada: `echo '<json>' | python3 -m coaching.research` con acciones `frame`, `grade`, `report`, `save`, como `coaching.tracker`.

Procedimiento `escala-skills/escala-strategy-research/SKILL.md` (`visibility: internal`, `owner: strategy`): pasos 1-6 de la experiencia, reglas que no se rompen, y cómo detectar búsqueda: el agente usa búsqueda sólo si su sesión le ofrece una herramienta de búsqueda web; si no, pasa a `sin_busqueda`. No se deduce por el nombre de la plataforma.

Gobierno: entrada en `catalog.yaml` y en `tests/test_capability_catalog.py` cambian **dos** aserciones (63 → 64, 64 → 65); palabras `mercado`, `competidores`, `tendencias`, `benchmark`, `investigar` en la ruta de Strategy con casos nuevos en `test_natural_requests_choose_an_explainable_first_capability`; `trigger` del especialista de strategy + regeneración de `adapters/claude|codex/agents/escala-strategy.*` (la prueba de deriva de `tests/test_s67_5_specialist_agents.py` lo exige).

### S83.2 — modo benchmark

Cómo lo hacen negocios comparables: precios, oferta/paquetes, canales, y métricas **publicadas**. Comparable = mismo `offer_category` + `geography` confirmados; competidores que el dueño no nombró quedan como "candidato" hasta que diga sí (regla de E71). Salida: tabla de máximo 5 comparables con fuente y fecha por celda; celda sin fuente = "no encontrado", nunca un estimado. Decisión típica: precio, paquete o canal.

### S83.3 — modo mercado

Cómo está su mercado: demanda, tipo de clientes, competidores, tamaño. Sin `segment` y `geography` confirmados no se calcula tamaño; se devuelve la pregunta que falta. Un tamaño nunca es un número solo: rango, método y supuestos, o "no estimable todavía" con el dato que lo permitiría (regla de E71). Fuentes que se contradicen se muestran ambas, no se promedian. Decisión típica: entrar/crecer en un segmento o zona.

### S83.4 — modo fortalezas/debilidades y tendencias

Posición frente al mercado (reusa los comparables de S83.2 si existen y siguen vigentes) y tendencias con fecha que afectan al negocio. No escribe un SWT: devuelve `ResearchClaim` que `escala-strategy-swt` incorpora como evidencia externa marcada ("según fuentes externas, [fecha]"), separada de la evidencia interna que ya usa. Paso final nuevo en `escala-strategy-swt`: "¿Quieres que revise qué dicen fuera de tu empresa antes de cerrar el SWT?". Decisión típica: qué fortaleza apalancar o qué tendencia atender este trimestre.

### S83.5 — integración con el diagnóstico y verificación por plataforma

- `to_diagnostic_inputs(report) -> DiagnosticInputs`: la decisión confirmada → un `DiagnosticEvidence` con `source_kind="conversation"`, `answer_status="fact"`, `source_ref` = ruta local del reporte, `decision` = área de la decisión; cada afirmación externa → una línea en `assumptions` con estado, fuentes y fecha; lo no encontrado → `open_questions`. No se cambia `coaching/diagnose/models.py`. Por verificar en la historia: que el texto de la decisión pase `_is_detailed_narrative`.
- Un reporte vencido (`review_by` pasado) entra con `freshness="stale"` y ESCALA ofrece actualizarlo antes de usarlo.
- Ruta de entrada desde el diagnóstico: cuando la restricción principal es de Strategy o de Cash por precio/margen, la propuesta de ruta de E75 incluye el modo que corresponde (tabla D2). Si E75 S75.3 aún no existe, el procedimiento de diagnóstico sólo ofrece la investigación como siguiente paso en texto; no se simula el hand-off.
- Matriz verificada por plataforma: con búsqueda / sin búsqueda, cómo se detecta, comando o pasos para reproducir. Superficies: Claude Code, Codex, Claude (claude.ai / Desktop) si ESCALA corre ahí. ChatGPT Work queda como "no verificado" hasta E85.

## Contratos clave

- Ninguna búsqueda lleva datos privados de la empresa; lo prueba el test de privacidad de S83.1.
- El conocimiento del modelo no es fuente. Puede sugerir **qué buscar**, nunca **qué es verdad**.
- `confirmado` = ≥ 3 fuentes independientes con fecha; todo lo demás se dice "por confirmar".
- Toda investigación termina en una decisión elegida por el dueño (incluida "todavía no, primero consigo X para el [fecha]").
- Todo lo persistido va a `.escala/my-company/research/` (local, ignorado por git). Tests sólo con fixtures sintéticos.
- Las URLs no salen del reporte: el diagnóstico y los facts sólo guardan la ruta local del reporte.

## Incógnitas del scope — decisiones propuestas

### U1. Comportamiento sin búsqueda web

**Decisión propuesta — pendiente de confirmar por el dueño.** Modo "con tus fuentes" (D3): el dueño aporta 2-3 fuentes; las reglas de confirmación no se relajan (lo normal será "por confirmar"); el reporte abre con el límite y dice qué fuente subiría cada hallazgo; nunca se usa la memoria del modelo como evidencia. La presencia de búsqueda se decide por la herramienta disponible en la sesión, no por la plataforma.

Por qué: (1) sigue siendo útil en cualquier cliente sin prometer lo que no está verificado; (2) mantiene la regla del especialista de strategy ("never present market claims without source and date"); (3) la memoria del modelo no tiene fecha ni fuente verificable, así que presentarla como investigación contradice el propio "Fuera" del scope. Alternativa descartada: negarse a investigar sin búsqueda (deja al dueño sin nada y lo manda a otra herramienta).

Estado por plataforma (nada de esto está verificado para un empresario; se verifica en S83.5):

| Plataforma | Búsqueda web para ESCALA | Estado |
|---|---|---|
| Claude Code | La herramienta `WebSearch` aparece en la sesión del dueño (observado 2026-09-30) | No verificado en la instalación de un empresario |
| Claude (claude.ai / Desktop) | Desconocido | No verificado; tampoco está verificado que ESCALA corra ahí |
| Codex | Desconocido | No verificado |
| ChatGPT Work | Desconocido | No verificado; ESCALA no corre ahí hasta E85 |

### U2. Orden de módulos: fijo o elegido por la restricción

**Decisión propuesta — pendiente de confirmar por el dueño.** Lo elige ESCALA según la restricción diagnosticada, uno por conversación, con una línea de por qué; el dueño puede cambiarlo (D2). Si el dueño pide un modo con sus palabras, gana su pedido.

| Restricción o pedido | Modo que ESCALA propone |
|---|---|
| Cash por precio o margen; "¿cuánto cobran los demás?" | benchmark |
| Strategy por demanda, clientes, crecimiento o zona nueva; "¿cómo está mi mercado?" | mercado |
| Planeación del trimestre / SWT; "¿qué viene para mi sector?" | fortalezas-tendencias |
| People o Execution | Ninguno se propone (el freno es interno); sólo si el dueño lo pide |
| Sin diagnóstico y pedido vago ("quiero investigar") | Una pregunta: "¿Qué decisión quieres tomar con esto?" y se mapea |

Por qué: (1) E75 ya decidió que el usuario no sigue un orden editorial y que el diagnóstico propone como máximo dos rutas; un orden fijo contradice eso; (2) un orden fijo son tres investigaciones antes de la primera decisión útil, lo contrario de "ultra simple"; (3) no proponer investigación en People/Execution evita ruido. Alternativa descartada: orden fijo benchmark → mercado → fortalezas (más fácil de explicar, pero retrasa la decisión y obliga a investigar lo que no frena al negocio).

## Otras incógnitas abiertas (no se afirman)

- U3: si `_is_detailed_narrative` acepta el texto de una decisión confirmada tal cual (S83.5 lo verifica; si no, se ajusta el texto, no el validador).
- U4: si E75 S75.3 (elegir ruta) llega antes que S83.5; si no, la entrada desde el diagnóstico es una sugerencia en texto.
- U5: cuántas fuentes independientes con fecha se encuentran para negocios locales pequeños; puede que casi todo quede "por confirmar". Es honesto, pero hay que ver en S83.2 si la experiencia sigue siendo útil.
- U6: ventana de frescura de 90 días para todo (D6); puede requerir una por modo si S83.3 lo muestra.

## Revisión adversarial

`design.redteam.json`: los hallazgos `wrong`/`weak` se incorporan arriba.

### Machine
```yaml
modules_affected:
  - path: coaching/research/
    change: create
  - path: coaching/research/tests/
    change: create
  - path: escala-skills/escala-strategy-research/SKILL.md
    change: create
  - path: escala-skills/catalog.yaml
    change: modify
  - path: tests/test_capability_catalog.py
    change: modify
  - path: escala_server/specialist_team.py
    change: modify
  - path: adapters/specialists/contract.json
    change: modify
  - path: adapters/claude/agents/escala-strategy.md
    change: modify
  - path: adapters/codex/agents/escala-strategy.toml
    change: modify
  - path: escala-skills/escala-strategy-swt/SKILL.md
    change: modify
decisions:
  - id: D1
    choice: "Un solo procedimiento interno escala-strategy-research con tres modos, alcanzado desde escala vía el especialista de strategy o la ruta propuesta por el diagnóstico"
    rationale: "Una sola puerta y el mínimo de superficie; las reglas de investigación viven en un sitio"
    constraint: "Ningún comando, alias, especialista ni capacidad MVP nueva"
  - id: D2
    choice: "El modo lo propone ESCALA según la restricción diagnosticada (tabla U2), uno por conversación; el pedido explícito del dueño gana (decisión propuesta)"
    rationale: "E75: sin orden editorial, máximo dos rutas; llegar rápido a una decisión"
    constraint: "No proponer investigación para restricciones de People o Execution salvo pedido"
  - id: D3
    choice: "Sin búsqueda web: modo con fuentes del dueño, mismas reglas de confirmación, límite declarado (decisión propuesta)"
    rationale: "Útil en cualquier cliente sin prometer capacidades no verificadas"
    constraint: "La memoria del modelo nunca es fuente; no se deduce búsqueda por el nombre de la plataforma"
  - id: D4
    choice: "Confirmado = 3 o más fuentes independientes con fecha; todo lo demás es por confirmar"
    rationale: "Disciplina de rai-research adaptada; regla del especialista de strategy"
    constraint: "Nunca presentar como hecho algo con una fuente o sin fecha"
  - id: D5
    choice: "Cada investigación termina en 2-3 opciones, una recomendación y la decisión que elige el dueño (incluida 'todavía no' con dato y fecha)"
    rationale: "Principio del dueño: cada módulo termina en una decisión"
    constraint: "No guardar una decisión sin el sí del dueño"
  - id: D6
    choice: "Frescura única de 90 días (review_by) para todos los modos (decisión propuesta)"
    rationale: "Simple primero; precios y mercado cambian por trimestre"
    constraint: "Reporte vencido entra al diagnóstico como stale"
  - id: D7
    choice: "El diagnóstico recibe la decisión confirmada como evidencia 'conversation'/'fact' con la ruta local del reporte; lo externo va a assumptions y lo no encontrado a open_questions"
    rationale: "No cambia el contrato de E49/E75 y respeta require_local_ref"
    constraint: "Ninguna URL en facts ni en DiagnosticEvidence; coaching/diagnose/models.py no cambia"
  - id: D8
    choice: "E83 absorbe el contrato, encuadre, mercado, competidores y brief de E71; el customer journey de E71 (S71.5) pasa a E84 (decisión propuesta)"
    rationale: "Evitar dos contratos de research para lo mismo"
    constraint: "E83 no edita archivos de E71; la disposición de E71 la aplica el dueño"
  - id: D9
    choice: "El modo fortalezas-tendencias alimenta a escala-strategy-swt en vez de producir su propio SWT"
    rationale: "Un solo SWT canónico"
    constraint: "No crear un segundo artefacto SWT"
constraints:
  - "Test de privacidad en S83.1: ninguna búsqueda generada contiene nombre de empresa, personas ni cifras de la empresa sintética"
  - "Reportes sólo en .escala/my-company/research/ (ignorado por git); los escribe el módulo, no el especialista"
  - "Tests sólo con fixtures sintéticos; nada de ~/Downloads, .escala/ reales ni .scaleup/"
  - "No afirmar búsqueda web en ninguna plataforma sin la matriz verificada de S83.5; ChatGPT Work no verificado hasta E85"
  - "Texto al usuario en español llano, sin jerga interna ni nombres de procedimientos"
  - "Catálogo: dos aserciones cambian (63 -> 64, 64 -> 65)"
  - "Tipos completos, modelos Pydantic, pyright strict"
```
