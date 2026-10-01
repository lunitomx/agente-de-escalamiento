# ESCALA-52 — Auditoría: ultra sencillo y poderoso para el usuario final

**Tipo:** primera pasada, sólo lectura del repo · **Fecha:** 2026-09-30 · **Revisó:** especialista UX (AhuehueteUX)
**Producto:** ESCALA · **Rol revisado:** dueño de pequeña empresa en México, no técnico, que llega por primera vez o vuelve a su reunión del grupo de accountability.
**Objetivo del dueño:** en menos de un minuto de conversación, sentir que alguien entendió su problema y le dijo qué hacer.

## Cómo leer este reporte

- **Evidencia** es lo que está escrito en el repo, con `archivo:línea`. **Supuesto** es lo que creo que pasa pero sólo se confirma con una sesión real; lo marco así.
- No leí `.escala/`, `.scaleup/`, `~/Downloads` ni datos reales del tracker.
- No se ejecutó ESCALA con una persona. Todo lo que depende de ver la reacción de un dueño queda en la sección **Requiere usuarios reales**.
- Escala de color: **verde** = cumple la meta, **amarillo** = cumple a medias o sólo en una plataforma, **rojo** = el dueño se atora o ve cosas que no debería.

---

## 1. Scorecard

| # | Punto | Color | En una línea |
|---|---|---|---|
| 1 | Primer minuto | **Rojo** | Antes de la primera respuesta útil hay 6–8 pasos técnicos (terminal, Git, Python, `uv`, clonar, instalador con banderas). La meta era 3. |
| 2 | Superficie | **Amarillo** | El diseño es bueno (1 puerta pública, 65 procedimientos internos), pero hay 28 procedimientos que todavía recomiendan `/escala-…` y en esta máquina el menú muestra 56 comandos viejos. |
| 3 | Proactividad | **Amarillo** | Prioridades → hoja del grupo y diagnóstico → investigación sí se ofrecen. Pero la puerta `escala` no sabe que existen hoja, investigación, recorrido del cliente ni tableros. |
| 4 | Paridad Claude / Codex / ChatGPT | **Rojo** | Sólo Claude Code está verificado. Los textos dicen "tu Claude". ChatGPT no existe todavía y la promesa de privacidad no aplica ahí. |
| 5 | Conexión Drive / hoja | **Amarillo** | La privacidad es ejemplar y el texto es claro. Pero el dueño sigue copiando y pegando bloques, y la conexión depende de un menú de Claude. |
| 6 | Lenguaje | **Amarillo** | Los módulos nuevos (hoja, recorrido, tableros) están en español llano. El saludo y los módulos viejos usan People/Strategy/Cash, CCC, BHAG, SWT, OPSP, Deep Dive. |
| 7 | Errores | **Amarillo** | Hay buenos mensajes para "no hay búsqueda", "no es tu pestaña" y "falta dato". No hay mensaje para "falló el programa" ni para "Python no está". |
| 8 | Poder (cada módulo termina en decisión) | **Verde/Amarillo** | Hoja, investigación, recorrido y tableros cierran con una decisión. El diagnóstico cierra con una pregunta ("preparar el Deep Dive") y Cash sólo recomienda el siguiente cálculo. |

---

## 2. Evidencia por punto

### 2.1 Primer minuto — Rojo

**Lo que el dueño hace hoy, en orden** (`PILOTO-EMPRESARIOS.md`, `README.md`):

1. Instalar Git, Python 3, `uv` y un agente de terminal: "Necesitas Git, Python 3, `uv` y uno de estos agentes locales: Claude Code, Codex CLI o Hermes Agent." (`PILOTO-EMPRESARIOS.md:16-17`). En Windows, además "usa WSL2" (`:19`).
2. "Abre una terminal y ejecuta:" (`:23`).
3. `git clone …` (`:26`).
4. `cd agente-de-escalamiento` (`:27`).
5. `./install.sh --platform claude` (`:28`). Para eso tiene que elegir entre `--platform`, `--all-platforms`, `--skills-only`, `--with-specialists` y `--with-rai-mcp` (`README.md:25-33`, `install.sh:20-30`).
6. "Después abre tu agente en esa carpeta" (`PILOTO-EMPRESARIOS.md:34`).
7. Escribir su preocupación. El saludo le responde "Trabajo contigo sobre People, Strategy, Execution y Cash." (`escala-skills/escala-welcome/SKILL.md:26`).
8. La guía le pide: "Elige un foco: Cash, People, Strategy o Execution." (`PILOTO-EMPRESARIOS.md:43`). Eso contradice la puerta, que dice "No le pidas elegir un skill, carpeta, slash-command ni metodología" (`escala-skills/escala/SKILL.md:14-15`).

**Decisiones antes de recibir algo útil:** plataforma, banderas del instalador, carpeta, foco. Son cuatro, y tres son técnicas.

**Lo que sí está bien:** una vez dentro de la conversación, la bienvenida pide una sola pregunta por turno (`escala-welcome/SKILL.md:16`, `:87-88`) y ataca el dolor sin dar un tour (`:18`). La meta interna es "<10 min" (`:74`). No es "el primer minuto", pero va en la dirección correcta.

**Lectura de capas (Garrett):** no se arregla con pantallas ni con textos. Es un problema de **estrategia y alcance**: el canal (terminal más repo) no corresponde a la persona (dueño no técnico). La ruta A del spike, directorio de plugins en ChatGPT/Codex con "≈3 pasos" (`work/epics/e85-chatgpt-dots-ready-specialists/s85.1-spike.md`, sección 2), es hoy la única que cumple la meta.

### 2.2 Superficie — Amarillo

- **El diseño cumple la meta:** `public_entrypoint: escala` (`escala-skills/catalog.yaml:5`). Sólo `escala` es `visibility: public` (`:8`). El instalador enlaza un solo skill y borra los demás enlaces `escala-*` (`install.sh:263-284`). Las retros de E82–E84 repiten "ningún comando nuevo para el dueño".
- **Tamaño del catálogo interno:** 65 procedimientos más 39 aliases heredados (`catalog.yaml:2-4`). No es un problema mientras el dueño no los vea.
- **Fugas hacia el dueño:**
  - 28 `SKILL.md` todavía mencionan `/escala-…` como siguiente paso. Ejemplo de Cash, que el dueño toca seguido: "| Sin trabajo previo | `/escala-cash-ccc` — mapear CCC |" (`escala-skills/escala-cash/SKILL.md:31-33`). Otros: `escala-export/SKILL.md:68` ("Suggest running `/escala-diagnose` or `/escala-welcome`"), `escala-execution-rhythms/SKILL.md:46`, `escala-cash-acceleration/SKILL.md:42`. Si el agente sigue el procedimiento al pie de la letra, el dueño ve un comando.
  - `escala-bugreport/SKILL.md:32` sigue diciendo "**Activación:** `/escala-bugreport`".
  - **En esta máquina** hay 56 enlaces `~/.claude/skills/escala-*` que apuntan al repo viejo `agente-de-escalamiento`. En la sesión de Claude Code aparecen como 56 comandos. Un dueño que instaló antes del cambio y nunca reinstaló ve el menú técnico completo. **Supuesto:** que eso le pase a dueños reales. Para verificarlo: `ls ~/.claude/skills | grep -c escala` en la máquina de un piloto.
- **Qué fusionar o esconder** (vista del dueño): People, Strategy, Execution y Cash no deberían aparecer como nombres. Bastan tres cosas visibles en lenguaje del dueño: "¿Qué te preocupa?", "Prepárame para mi reunión" y "¿Cómo voy?". Lo demás son pasos internos.

### 2.3 Proactividad — Amarillo

**Lo que sí ofrece sin que el dueño sepa que existe:**
- Al terminar prioridades: "¿Las pasamos a tu hoja del grupo?" (`escala-skills/escala-execution-prioridad/SKILL.md:66`, `escala-execution-priorities/SKILL.md:40`).
- En el diagnóstico, si el freno es de mercado o precio: "Si quieres, antes de decidir vemos cómo cobran negocios parecidos / cómo está tu mercado, sin usar datos de tu empresa en las búsquedas" (`escala-diagnose/SKILL.md:163-165`).
- Recorrido del cliente: "Para ver dónde se te van los clientes, ¿me cuentas cómo llega un cliente hasta que te compra? Son 5 preguntas cortas. Si prefieres, lo vemos después." (`coaching/journey/messages.py:10-14`). Es el mejor texto de ESCALA: dice el beneficio, el costo y una salida.
- Tableros: "¿Qué quieres decidir con ese tablero? …" (`escala-dashboard/SKILL.md:45`).

**Huecos:**
- **La puerta no conoce los módulos nuevos.** `escala/SKILL.md:21-23` manda leer `capabilities/mvp/catalog.json`, que tiene seis capacidades: diagnóstico, OPPP, visión, prioridad trimestral, ritmo de juntas y revisión trimestral (`catalog.json:40-85`). No incluye hoja del grupo, investigación, recorrido del cliente ni tableros, y `escala/SKILL.md` no los nombra. Las rutas de `catalog.yaml:338-414`, que sí cubren "tablero", no las lee ningún procedimiento en ejecución. Sólo las usan `scripts/qualify_e42_s42.4.py` y `scripts/refresh_legacy_skill_aliases.py`. **Supuesto, de alto riesgo:** que en una instalación real `escala` no llegue a E82–E84 si el dueño no usa las palabras exactas, porque sólo se instala el skill `escala` y los especialistas son opcionales (`--with-specialists`, `install.sh:27`). La guía del piloto no los menciona.
- **El diagnóstico todavía no conecta solo:** "La elección de ruta automática (E75 S75.3) aún no existe: no simules el traspaso" (`escala-diagnose/SKILL.md:166-167`).
- **Contradicción de ruta:** "ventas" lleva a Cash (`catalog.yaml:353`), mientras la puerta dice "Si cuenta que le compran poco, que no vende… es Strategy" (`escala/SKILL.md:34-35`). Un dueño que dice "bajaron mis ventas" puede terminar en un cálculo de caja en vez del recorrido del cliente.
- **No hay un "antes de tu reunión" por calendario.** El paso 7 del tracker sólo se activa "Cuando el empresario mencione su reunión" (`escala-execution-tracker/SKILL.md:134`).

### 2.4 Paridad — Rojo

- "Matriz por plataforma: sólo el núcleo verificado por tests; Codex, claude.ai/Desktop y ChatGPT Work (E85) sin verificar." (`work/epics/e84-customer-journey-local-dashboards/retrospective.md`, sección Pendiente).
- El texto de conexión es exclusivo de Claude: "Para leer tu hoja, conecta Google Drive en tu Claude (Configuración → Conectores)." (`coaching/tracker/messages.py:49-50`). En Codex esa instrucción no aplica, y no hay variante.
- "No prometas pasos para ChatGPT: hoy sólo está verificado Claude (E85)." (`escala-execution-tracker/SKILL.md:26`). Es honesto, pero deja a ese dueño sin camino.
- ChatGPT: el spike recomienda "S85.2 … no construir todavía" y aclara que la promesa "Nunca… envíes información fuera de la carpeta local" (`escala/SKILL.md:47-48`) "no se puede cumplir en Work Cloud ni en un dot" (`s85.1-spike.md`, sección 5c). La misma frase significaría cosas distintas en cada plataforma.
- La búsqueda en internet en investigación sí está pensada como neutral a la plataforma: "puedes prenderla en el menú de herramientas o en la configuración de este asistente" (`coaching/research/messages.py:21-22`). Ese es el patrón que falta en el tracker.

### 2.5 Conexión Drive y hoja — Amarillo

**Los pasos reales hoy** (`escala-execution-tracker/SKILL.md:49-130`):

1. "¿Cómo te llamas? Con tu nombre busco tu pestaña en la hoja del grupo." (`messages.py:27`)
2. Conectar Drive en Configuración → Conectores, o copiar la pestaña completa y pegarla (`messages.py:49-51`), con el aviso "Ojo: al conectarlo, el asistente puede ver todo el archivo compartido del grupo; ESCALA sólo usa tu pestaña." (`:31-32`)
3. "Veo una pestaña que se llama **Ana**. ¿Es la tuya?" (`:87`) y luego el sí.
4. "¿Para qué mes son estos compromisos?" (`:127`)
5. Leer la tabla propuesta, copiar el bloque y pegarlo: "Copia este bloque y pégalo ahí (Ctrl+V; Cmd+V en Mac)" (`:272`), en la celda indicada (`:199-200`). A veces antes tiene que "Haz clic derecho en el número de la fila … y elige «Insertar 1 fila arriba»" (`:193-195`).
6. Repetir 4 y 5 para los Rocks.
7. Antes de la reunión: "¿Qué fecha es hoy? Con eso veo qué está vencido." (`:409`). El agente ya sabe la fecha; preguntarla es fricción gratuita.
8. Pasar a Done copiando otro bloque, y después borrar a mano: "selecciona sus celdas y presiona Supr (Delete en Mac). No elimines la fila completa." (`:406-407`)

**Lo excelente:** el mensaje de deshacer (`:142-144`, "No uses «Restaurar esta versión»: borraría lo que los demás escribieron") aplica recuperación de errores al estilo de Norman. La regla de nunca elegir pestaña sola (`SKILL.md:20`) y la de no leer pestañas ajenas antes del sí (`:17-19`) también.

**La fricción:** copiar y pegar sigue siendo el trabajo del dueño. Hay entre 2 y 4 operaciones manuales por mes, cada una con riesgo de pegar en la celda equivocada. El riesgo de que pegar rompa los menús desplegables de la plantilla sigue sin probar (`e82…/retrospective.md`, "U5"). Escribir directo en la hoja quedó en "ningún GO" (S82.6) y sigue sin verificar en ChatGPT (`s85.1-spike.md`, sección 3).

### 2.6 Lenguaje — Amarillo

**Bien** (español llano, sin jerga): `coaching/journey/messages.py` completo. Ejemplo: "Listo, quedó guardado sólo en tu computadora; no se publica. En 3 meses te pregunto si sigue igual." (`:31-33`). También los mensajes de deshacer del tracker y `research/messages.py:30`: "¿Qué vendes exactamente y en qué ciudad o zona? Con eso armo las búsquedas."

**Mal** (lo ve el dueño):

| Texto | Dónde | Problema |
|---|---|---|
| "Trabajo contigo sobre People, Strategy, Execution y Cash." | `escala-welcome/SKILL.md:26` | Primera frase del producto, con cuatro palabras en inglés |
| "Elige un foco: Cash, People, Strategy o Execution." | `PILOTO-EMPRESARIOS.md:43` | Inglés, y además obliga a decidir |
| "Dime cuál es (Cash, Strategy, Execution o People) o déjala vacía." | `coaching/tracker/messages.py:247-248`, `:375-376` | Inglés; el dueño no sabe qué área es |
| "¿Quieres que revise qué dicen fuera de tu empresa antes de cerrar el SWT?" | `coaching/research/messages.py:57`; `escala-strategy-swt/SKILL.md:51` | SWT es una sigla sin explicar |
| "Tu CCC subió Q2→Q3→Q4…" / "Cambiaste el BHAG 3 veces…" | `escala-memory-alerts/SKILL.md:21`, `:32` | Siglas, aunque `escala-cash/SKILL.md:43` pide "días en cobrar" en vez de "DSO" |
| "Cash: reducir CCC de 67 a 50 días." | `escala-execution-prioridad/SKILL.md:33` | Igual que arriba |
| "necesito mi OPSP" | `README.md:88` | Pone la sigla como ejemplo de lo que el dueño diría |
| "termina con una pregunta concreta que prepare el Deep Dive" | `escala-diagnose/SKILL.md:157-158` | Instrucción interna; si se filtra, el dueño la ve en inglés |

**Caso aparte, justificado a medias:** "Done", "Rocks", "Critical Number", "Monthly Commitments", "START HERE" (`tracker/messages.py:37`, `:171`, `:208`, `:288`) son los nombres que trae la plantilla del grupo. Se usan para que el dueño encuentre la celda. Conviene traducirlos la primera vez ("tus metas del trimestre (Rocks)"), como ya se hace en `:171` y `:288`.

### 2.7 Errores — Amarillo

| Situación | Lo que ve el dueño | Evaluación |
|---|---|---|
| Sin búsqueda en internet | "Aquí la búsqueda en internet está apagada: puedes prenderla … o pégame dos o tres fuentes …" (`research/messages.py:21-24`) | **Bien**: explica, da salida y pone límite |
| Pestaña ajena o dudosa | "Antes de leer tu pestaña necesito que me confirmes que es la tuya." (`tracker/messages.py:35`); si no hay coincidencia, lista los nombres de todas las pestañas (`:78-79`) | **Bien**. Matiz: mostrar los nombres de los demás es aceptable porque sólo son nombres de pestaña (`SKILL.md:17`) |
| Archivo distinto al de la vez pasada | "Este archivo no es el que usamos la otra vez. …" (`:129-130`) | **Bien** |
| Archivo sin pestañas o vacío | "No encontré pestañas en el archivo. ¿Me pegas aquí tu pestaña?" (`:40`) | Bien |
| Sin datos para tablero | "sin números no hay tablero"; muestra «Falta» (`e84…/retrospective.md`; `escala-dashboard/SKILL.md:87`) | Bien |
| Sin conexión a Drive o permiso negado | Sólo existe la instrucción de conectar (`:49-51`). No hay texto para "lo conecté y no aparece el archivo" ni para "no tengo permiso" | **Falta** |
| Falla el programa (Python ausente, `.venv` roto, `--skills-only`) | `coaching/tracker/__main__.py:13-19` no atrapa excepciones: el agente recibe un traceback y lo traduce a su manera | **Falta**: no hay mensaje fijo |
| Cash sin servidor | `escala-cash/SKILL.md:38`: "usar `POST /api/cash/power-of-one`". **Supuesto:** si el servidor no está corriendo, falla sin mensaje para el dueño | **Por verificar** |

### 2.8 Poder — Verde/Amarillo

- **Terminan en decisión:**
  - Tracker: "¿Qué hacemos con «…»: nueva fecha o ya no va?" (`tracker/messages.py:522`).
  - Investigación: "Quieres decidir: {…}. Voy a buscar: {…}. No llevo tu nombre ni tus cifras. ¿Va, o cambio algo?" (`research/messages.py:181-182`), y guarda la decisión (`:188-190`).
  - Recorrido: "¿Qué hacemos con esto?" (`journey/messages.py:27`).
  - Tableros: `construir|esperar|no` (`escala-dashboard/SKILL.md:60`).
- **Terminan en información o en otra pregunta:**
  - El diagnóstico: "Propón uno o dos focos con su razón. Espera elección… Hasta que E65 entregue procedimientos verificados, termina con una pregunta concreta" (`escala-diagnose/SKILL.md:156-158`). El módulo que más usa un dueño nuevo cierra sin una acción para esta semana.
  - Cash: la tabla de `escala-cash/SKILL.md:29-34` sólo encadena cálculos (CCC → Power of One → aceleración). "El asesor debe recomendar después de cada cálculo" (`:46`) es una intención, no un contrato.
- **Le cargan trabajo al dueño:** "Abre cada enlace y dame el texto de la página; reviso si la cita está ahí." (`research/messages.py:205-206`) y "Reescríbelo en 10 palabras o menos, sin «/» ni links…" (`:225-227`). Las dos tienen razones de rigor, pero el dueño acaba editando el trabajo de ESCALA.

---

## 3. Hallazgos priorizados

Impacto (I) y esfuerzo (E) van en Alto, Medio o Bajo. El orden dentro de cada grupo es por impacto sobre esfuerzo.

### Quitar

**Q1. Quitar los nombres en inglés de las cuatro áreas de todo lo que ve el dueño.** I: Alto · E: Bajo
- *Hoy:* Doña Lupita, dueña de una tortillería en Puebla, abre ESCALA y lee "Trabajo contigo sobre People, Strategy, Execution y Cash". Luego la guía le pide "Elige un foco". No sabe qué es Execution y elige Cash porque es la única palabra que reconoce.
- *Después:* "Hola, soy ESCALA. Te ayudo a ordenar tu negocio. ¿Qué es lo que más te preocupa hoy?" Las áreas se nombran como "tu equipo, tus clientes, tu día a día, tu dinero". El área técnica queda en el dato interno, nunca en pantalla.
- Archivos: `escala-welcome/SKILL.md:26`, `:39`; `PILOTO-EMPRESARIOS.md:3`, `:43`; `tracker/messages.py:247-248`, `:375-376`.

**Q2. Quitar todas las recomendaciones `/escala-…` de los procedimientos internos.** I: Alto · E: Bajo
- *Hoy:* Don Ramón pregunta por su flujo de caja. ESCALA termina con "Siguiente: `/escala-cash-power1` — Power of One". Él lo escribe tal cual y no pasa nada, porque ese comando ya no está instalado.
- *Después:* "¿Vemos cuánto dinero liberas si cobras 10 días antes?" ESCALA sigue sin mostrar el nombre del procedimiento.
- Son 28 archivos (`grep -rln '\`/escala-' escala-skills/*/SKILL.md`). Agregar un test que falle si un `SKILL.md` interno contiene `/escala-`.

**Q3. Quitar "¿Qué fecha es hoy?"** I: Medio · E: Bajo
- *Hoy:* antes de la reunión, ESCALA le pregunta la fecha (`tracker/messages.py:409`).
- *Después:* el procedimiento manda `today` con la fecha del sistema y sólo pregunta si no la tiene.

**Q4. Quitar los comandos viejos de instalaciones anteriores.** I: Medio · E: Bajo
- *Hoy:* quien instaló antes del cambio ve 56 comandos `escala-*` en su menú.
- *Después:* `update.sh` borra los enlaces `escala-*` de cualquier repo, no sólo los del actual, y avisa: "Quité 55 atajos viejos; ahora sólo hablas con ESCALA."
- **Por verificar** con `ls ~/.claude/skills | grep -c escala` en la máquina de un piloto.

### Simplificar

**S1. Instalación de un solo paso para el dueño.** I: Alto · E: Alto
- *Hoy:* son 8 pasos (sección 2.1) y requieren terminal, Git, Python y `uv`.
- *Después:* a corto plazo, un solo comando copiable sin banderas (`curl … | sh`) que instala lo necesario en Claude Code, incluidos los especialistas. A mediano plazo, la ruta A del spike: buscar "ESCALA" en Plugins, instalar y escribir (≈3 pasos).
- Esto es estrategia de canal, no de interfaz. Mientras siga en terminal, ESCALA no es para el dueño no técnico sin un acompañante.

**S2. Una sola lista de capacidades para la puerta.** I: Alto · E: Medio
- *Hoy:* la puerta lee `catalog.json`, con 6 capacidades sin hoja, investigación, recorrido ni tableros, y las rutas de `catalog.yaml` no las consume nadie en ejecución. Un dueño que dice "prepárame para mi junta del grupo" puede recibir una respuesta genérica.
- *Después:* `catalog.json` (o lo que lea `escala/SKILL.md`) incluye los cuatro módulos de E82–E84 con sus frases disparadoras. `escala/SKILL.md` dice en una línea dónde viven los procedimientos internos. Un test comprueba que cada procedimiento `keep` de `catalog.yaml` sea alcanzable desde la puerta.
- Corregir de paso la ruta "ventas" → Cash (`catalog.yaml:353`) para que respete `escala/SKILL.md:34-35`.

**S3. Menos copiar y pegar en la hoja.** I: Alto · E: Medio
- *Hoy:* Ana copia un bloque, busca la celda F23, inserta filas, pega, revisa y repite para los Rocks. Al mes siguiente vuelve a pasar terminados a Done y borra celdas a mano.
- *Después, sin escritura directa:* (a) proponer compromisos y Rocks en un solo bloque y una sola celda cuando la plantilla lo permita; (b) en vez de "pasa a Done y luego borra", un único bloque ya ordenado para la sección completa; (c) cerrar con "Cuando lo pegues, dime 'listo' y reviso que quedó bien" y volver a llamar a `prepare`.
- *Después, con escritura verificada* (M4 del spike / P2 de S82.6): "¿Lo escribo yo en tu pestaña? Sólo toco las celdas F23 a F25." con confirmación por cambio.

**S4. Diagnóstico que cierra con una acción de esta semana.** I: Alto · E: Medio
- *Hoy:* el diagnóstico propone "uno o dos focos" y termina con una pregunta que prepara otra sesión (`escala-diagnose/SKILL.md:156-158`).
- *Después:* "Tu freno principal es que cobras a 60 días. Esta semana: llama a tus 3 clientes más grandes y pide pago a 30. ¿Lo anoto como compromiso en tu hoja?" Así el diagnóstico desemboca en la hoja del grupo, que es el módulo con más tracción.

**S5. Investigación sin tarea de corrector para el dueño.** I: Medio · E: Medio
- *Hoy:* "Abre cada enlace y dame el texto de la página" (`research/messages.py:205-206`) y "Reescríbelo en 10 palabras o menos" (`:225-227`).
- *Después:* ESCALA propone la versión corta y el dueño sólo dice sí o la corrige. La verificación de citas va cuando haya búsqueda con lectura de página; si no la hay, el hallazgo queda "por confirmar" sin pedirle trabajo.

### Añadir

**A1. Mensaje fijo para "algo falló".** I: Alto · E: Bajo
- *Hoy:* si falta Python o el módulo truena, el dueño ve lo que el agente improvise a partir de un traceback.
- *Después:* cada `__main__.py` atrapa la excepción y devuelve `message`: "No pude abrir esa parte de ESCALA en tu computadora. No se perdió nada. Escribe 'reportar problema' y preparo un aviso para el equipo." Con test.

**A2. Mensajes de Drive para cuando no funciona.** I: Medio · E: Bajo
- Faltan tres casos: (a) "Conecté Drive pero no veo tu archivo. ¿Me pegas el link de la hoja?"; (b) "No tengo permiso para abrir ese archivo; pídele acceso a quien lo compartió o pega tu pestaña aquí."; (c) un texto por plataforma o neutral ("en la configuración de este asistente, en Conectores o Apps"), como ya hace `research/messages.py:21-22`.

**A3. "Antes de tu reunión" de forma proactiva.** I: Medio · E: Medio
- *Hoy:* sólo se activa si el dueño menciona la reunión.
- *Después:* al abrir la conversación, si hay pestaña confirmada y la reunión del grupo es en 3 días o menos (dato que el dueño dio una vez), la primera línea es "Tu reunión del grupo es el jueves. ¿Reviso tu hoja?" Respeta la regla de "una pregunta y sin insistir" de E84.

**A4. Promesa de privacidad que diga lo mismo en cada plataforma.** I: Medio · E: Bajo
- Reescribir `escala/SKILL.md:47-48` como consentimiento por plataforma, siguiendo la sección 5c del spike, antes de cualquier distribución en ChatGPT.

**A5. Glosario de una línea para los nombres de la plantilla.** I: Bajo · E: Bajo
- La primera vez que aparece cada término: "tu número clave (Critical Number)", "tus metas del trimestre (Rocks)", "terminado (Done)".

---

## 4. Epic propuesto: "ESCALA para el dueño: un minuto, una puerta, una decisión"

Objetivo: que un dueño no técnico reciba su primera recomendación accionable en 3 pasos o menos, sin jerga, en la plataforma que ya usa.

| Historia | Qué entrega | Tamaño (1–8) | Criterio verificable |
|---|---|---|---|
| S1 Lenguaje del dueño | Q1 + A5: áreas en español, siglas explicadas, glosario de plantilla | 3 | Un test recorre todos los textos para el dueño y falla si aparece `People|Strategy|Execution|Cash|CCC|BHAG|SWT|OPSP|Deep Dive` sin traducción al lado |
| S2 Cero comandos visibles | Q2 + Q4: limpiar 28 procedimientos y los enlaces viejos | 2 | `grep '/escala-' escala-skills/*/SKILL.md` = 0, salvo `escala`; `update.sh` deja exactamente 1 skill `escala*` |
| S3 Puerta que conoce todo | S2: catálogo único y alcanzabilidad; corregir ruta "ventas" | 5 | Test: cada procedimiento `keep` es alcanzable desde una frase del dueño; "bajaron mis ventas" lleva a Strategy |
| S4 Diagnóstico que termina en acción | S4: acción de esta semana y oferta de anotarla en la hoja | 3 | El último mensaje del diagnóstico tiene acción, responsable y fecha, más la oferta de la hoja si está confirmada |
| S5 Errores con salida | A1 + A2: excepción → mensaje; tres casos de Drive; texto neutral por plataforma | 3 | Test por módulo con Python roto simulado; ningún `message` dice "tu Claude" |
| S6 Hoja con menos pegado | Q3 + S3(a–c): fecha automática, un bloque por sección, "dime listo y reviso" | 5 | Preparar la reunión requiere 1 pegado o menos por sección; cero preguntas de fecha |
| S7 Reunión proactiva | A3 | 3 | Con reunión en 3 días o menos y pestaña confirmada, la primera línea la ofrece una sola vez; con "después" no se repite |
| S8 Instalación de un paso | S1 corto plazo: un comando, sin banderas, con especialistas | 5 | Medir en una máquina limpia: 3 pasos o menos y 0 decisiones técnicas hasta el primer "¿qué te preocupa?" |
| S9 Paridad y consentimiento | A4 + pruebas M2/M7 del spike en Codex, antes de ChatGPT | 3 | Misma frase de entrada y mismo cierre en Claude y Codex, con transcripciones guardadas |
| S10 Prueba con dueños reales | Sección 5 de este reporte | 2 | 3 sesiones grabadas con métricas llenas |

**Orden sugerido:** S2 → S1 → S5 → S3 → S4 → S10 (primera medición) → S6 → S7 → S8 → S9. Las primeras cuatro son baratas y cambian lo que el dueño ve hoy; S10 a la mitad evita invertir en S8 y S9 a ciegas.

**Fuera de alcance, a propósito:**
- Construir el adaptador de ChatGPT (lo decide E85 con M1–M3).
- Escritura directa en la hoja (depende de M4/P2).
- Rediseñar los tableros HTML.
- Tocar la lógica de cálculo de Cash.

---

## 5. Requiere usuarios reales — guion de prueba (2–3 personas del grupo de accountability)

**Preparación**
- Una computadora con ESCALA instalado por el equipo. La instalación se mide aparte, en la tarea 0.
- Empresa **sintética** o datos que la persona elija compartir. Una **copia** del tracker con su pestaña y dos pestañas de prueba.
- Grabar pantalla y voz con su permiso. Un facilitador que no ayuda; sólo dice "¿qué esperabas que pasara?".
- Duración: 40 minutos por persona.

**Tarea 0 — Instalar (opcional, 10 min tope).** Darle sólo `PILOTO-EMPRESARIOS.md`. Medir: pasos, momento en que pide ayuda, si termina.

**Tarea 1 — Primer minuto (5 min).** Consigna: "Cuéntale a ESCALA lo que más te preocupa de tu negocio esta semana."
- Medir: segundos hasta la primera respuesta útil; preguntas antes de recibir algo; palabras que no entendió (pedirle que las subraye en voz alta).
- Éxito: 3 intercambios o menos y cero palabras desconocidas.

**Tarea 2 — Sin saber que existe (8 min).** Consigna: "Dile que muchos le preguntan pero pocos le compran." No mencionar el recorrido del cliente.
- Medir: ¿ESCALA ofrece las 5 preguntas sin que las pida? ¿La persona acepta o pospone? Si pospone, ¿ESCALA insiste? (M3 de E84)

**Tarea 3 — Su hoja (10 min).** Consigna: "Pídele que te ayude con tu hoja del grupo para este mes."
- Medir: ¿entiende el aviso de Drive? ¿Confirma la pestaña correcta? ¿Pega en la celda correcta al primer intento? ¿Se rompió algún desplegable (U5)? ¿Cuántas veces copió y pegó?
- Éxito: filas correctas en su pestaña, nada tocado fuera de ella, y la persona explica cómo deshacer.

**Tarea 4 — Antes de la reunión (5 min).** Consigna: "Mañana tienes reunión del grupo."
- Medir: ¿le pregunta la fecha? ¿Entiende "Done", "Rocks" y "Critical Number"? ¿Toma una decisión sobre algún vencido?

**Tarea 5 — Algo falla (4 min).** Con la búsqueda apagada: "¿Cuánto cobra mi competencia?" Luego desconectar Drive y repetir la Tarea 4.
- Medir: ¿sabe qué hacer después del mensaje sin ayuda del facilitador?

**Cierre (3 min, preguntas fijas)**
1. "En una frase, ¿qué hace ESCALA?"
2. "¿Qué decidiste hoy gracias a ESCALA?" Si no puede nombrar una decisión, el punto 8 queda en rojo para esa persona.
3. "¿Qué palabra o paso te sobró?"
4. "Del 1 al 10, ¿qué tan probable es que lo uses antes de tu próxima reunión?"

**Repetir en Codex** con una de las 3 personas (Tareas 1 y 3) para medir paridad. ChatGPT queda para cuando M2 dé GO.

---

## 6. Cosas que no pude verificar en esta pasada

- Si una instalación limpia (`./install.sh --platform claude` sin `--with-specialists`) llega realmente a hoja, investigación, recorrido y tableros desde frases naturales. Es la verificación más urgente; prueba: Tareas 2 y 3 en una máquina limpia.
- Si `/api/cash/power-of-one` requiere que el dueño levante un servidor.
- Si `.escala/` del dueño vive dentro del clon del repo (README: "Abre una terminal en la carpeta local del producto" y luego "Abre tu agente … en esa carpeta"). Si es así, `git pull` y los datos del dueño comparten carpeta. Es un riesgo de soporte, no de interfaz.
