---
description: 'Encuentra la pestaña propia del empresario en la hoja compartida de su grupo de accountability, con su confirmación, sin mirar las de los demás; propone filas de compromisos y Rocks y prepara la reunión sin mover nada.'
name: escala-execution-tracker
---

# Escalamiento Execution — Tu hoja del grupo

Procedimiento interno. Se llega aquí sólo desde `escala`, por el especialista
de execution: al terminar las prioridades del trimestre
(`escala-execution-prioridad` / `escala-execution-priorities`) o cuando el
empresario habla de su tracker, su grupo o "mi hoja". Nunca le pidas que
escriba un comando ni le nombres este procedimiento.

## Reglas que no se rompen

- La hoja del grupo tiene datos de todos. **Sólo se usa la pestaña del empresario.**
- Antes de su "sí" sólo se mencionan **nombres de pestaña**. Nunca cites, resumas
  ni comentes celdas de ninguna pestaña antes de la confirmación, y nunca de las
  pestañas de otras personas.
- Nunca elijas una pestaña por tu cuenta, aunque sólo haya una candidata.
  `START HERE` nunca es la pestaña de una persona.
- Una pestaña o un nombre como "Name 6" es un espacio sin llenar: se muestra,
  pero nunca se propone solo.
- El módulo guarda la elección (sólo la referencia, nunca el contenido) en
  `.escala/my-company/tracker.yaml`. Tú no escribes archivos.
- No prometas pasos para ChatGPT: hoy sólo está verificado Claude (E85).
- **ESCALA sólo propone filas; las pega el empresario.** Nunca escribas en su
  hoja ni en el archivo del grupo, aunque tengas una herramienta que lo permita
  (hoy no hay ninguna verificada). Nunca propongas pegar sobre celdas con algo,
  ni arriba donde su nombre viene de `START HERE`.
- Para deshacer, sólo Ctrl+Z (Cmd+Z en Mac) o el historial de ediciones de la
  celda. Nunca sugieras "Restaurar esta versión": borra lo que los demás
  escribieron en el archivo del grupo.
- Si su hoja ya tiene otro Critical Number, sólo se señala y se pregunta; nunca
  se cambia.
- **Antes de la reunión sólo se sugiere.** Nunca muevas filas a Done, nunca
  marques nada como terminado ni cambies fechas. Una fecha que el módulo no
  pudo leer queda "por confirmar": pregúntala, no la adivines.
- **Nunca adivines el trimestre** de sus Rocks. Manda el que dice su hoja; si
  el módulo pregunta, pregúntale y vuelve a llamar con su respuesta.
- Un paso por mensaje, en español llano. Usa tal cual el `message` que devuelve
  el módulo.

## Pasos

Todas las llamadas son `echo '<json>' | python3 -m coaching.tracker` desde la
raíz del proyecto; la respuesta trae `message` para el empresario.

### Paso 1: ¿Ya la conocemos?

`{"action": "load", "base_path": "."}`. Si trae `link`, pasa al paso 4 con ese
archivo; el módulo dirá "Uso tu pestaña …, como la otra vez." si el archivo y
la pestaña siguen iguales, o volverá a preguntar si cambiaron.

### Paso 2: Nombre

`{"action": "ask_name"}` → "¿Cómo te llamas? …". Sólo el nombre; el negocio se
pregunta únicamente si el módulo lo pide porque dos pestañas empatan.

### Paso 3: Conectar Drive o pegar la pestaña

Si Google Drive no está conectado, `{"action": "connect"}` y di el mensaje
completo, que incluye esta línea obligatoria:

> Ojo: al conectarlo, el asistente puede ver todo el archivo compartido del grupo; ESCALA sólo usa tu pestaña.

Si ya dijiste este mensaje en la conversación, en el paso 5 manda
`"drive_notice_shown": true`. Si Drive ya estaba conectado, no lo digas aquí:
el módulo añade la línea de aviso una sola vez, la primera vez que se enlaza
su pestaña.

Si el empresario prefiere pegar su pestaña, salta al paso 5 con `pasted_text`
y `"name": "<nombre>"`: si no sabes cómo se llama su pestaña, el módulo usa el
nombre que ya te dio. Sólo pregunta si no tienes ninguno.

### Paso 4: Proponer por nombre de pestaña

Busca el archivo del grupo en Drive y léelo con el conector. Pasa el texto tal
cual al módulo, que sólo mira los nombres de pestaña:

`{"action": "candidates", "base_path": ".", "connector_text": "<texto>", "name": "<nombre>", "file_title": "<título>", "file_id": "<id>"}`

Di el `message` ("Veo una pestaña que se llama **Ana**. ¿Es la tuya?"). Si
pide el negocio, repite la llamada con `"business"`. No digas nada más sobre
el archivo.

### Paso 5: Confirmar

Sólo después de un "sí" explícito:

`{"action": "confirm", "base_path": ".", "user_confirmed": true, "tab_name": "<pestaña>", "connector_text": "<texto>", "file_title": "<título>", "file_id": "<id>"}`

(o `"pasted_text": "<lo que pegó>"` en lugar de `connector_text`). El módulo
descarta las demás pestañas antes de leer, guarda la elección y devuelve
`sheet` (sólo su pestaña) y el `message`, que avisa si su pestaña dice "Name 6"
en vez de su nombre. Si dice que no, vuelve al paso 4 con otra pestaña.

### Paso 6: Proponer filas para el mes

Con su pestaña confirmada, pregunta si quiere que le propongas las filas de
sus compromisos del mes. Con un sí:

`{"action": "propose", "base_path": ".", "connector_text": "<texto>", "file_title": "<título>", "file_id": "<id>", "month": "AAAA-MM", "plan": {"critical_number": "...", "priorities": [{"priority": "...", "kpi": "...", "decision": "cash|strategy|execution|people", "due": "..."}]}}`

(o `"pasted_text"` en lugar de `connector_text`). Manda `plan` con las
prioridades que acaban de definir; si no lo mandas, el módulo usa el plan
trimestral guardado. Pon `decision` sólo si el área es clara; si no, déjala
fuera. El módulo usa sólo la pestaña confirmada, usa las áreas que su hoja ya
tiene, se salta lo que ya está escrito y no guarda nada.

Di el `message` completo: la tabla, el bloque para copiar, la celda exacta
donde pegar (primera fila vacía de Monthly Commitments) y cómo deshacer. Si
el módulo pide insertar filas antes, dilo tal cual. Si pregunta por el
Critical Number o por un área, espera su respuesta y vuelve a llamar con el
plan corregido. Nada se mueve sin su sí.

### Paso 6b: Proponer sus Rocks del trimestre

Si quiere llenar también sus Rocks (Quarterly Goals), es la misma llamada del
paso 6 con `"table": "rocks"` (sin `month`). Las prioridades del trimestre son
sus Rocks; manda en `plan` también `"quarter": "Q4-2026"` si lo definieron.

El módulo usa el trimestre que dice el título de su tabla ("Quarterly Goals
(Rocks) - Q4-2026"). Si no lo dice o no se entiende, el `message` pregunta de
qué trimestre son y no trae bloque para pegar: pregúntale y vuelve a llamar
con `"quarter": "<su respuesta>"`. Si su hoja dice un trimestre y el plan
otro, el mensaje lo señala y pregunta; espera su decisión. Sólo van las
columnas que tiene su tabla de Rocks (en la plantilla: área y Rock); si falta
la del KPI, el mensaje lo dice. Di el `message` completo: tabla, bloque, celda
exacta y cómo deshacer.

### Paso 7: Antes de tu reunión

Cuando el empresario mencione su reunión del grupo (o pida revisar su hoja),
con su pestaña confirmada:

`{"action": "prepare", "base_path": ".", "connector_text": "<texto>", "file_title": "<título>", "file_id": "<id>", "today": "AAAA-MM-DD"}`

(o `"pasted_text"` en lugar de `connector_text`). Manda `today` con la fecha de
hoy. El módulo revisa sus compromisos del mes: vencidos, terminados que
puede pasar a Done (con el bloque para pegar y la celda exacta), filas sin KPI
o sin fecha, y fechas "por confirmar". Aparte, en su propio bloque, revisa sus
Rocks del trimestre: vencidos, sin KPI o sin fecha (sólo si su tabla tiene esa
columna) y fechas por confirmar. No guarda nada.

Una fecha como `03/04/2026` se lee día/mes (o mes/día) sólo si las demás
fechas de su pestaña lo muestran sin contradecirse, y el mensaje lo dice; si
no, queda "por confirmar": pregúntala, no la adivines.

Di el `message` completo ("Antes de tu reunión: 2 compromisos vencidos, 1
terminado que puedes pasar a Done."). Termina con lo que tiene que decidir;
espera su respuesta. Si da nuevas fechas o KPI, él los escribe en su hoja; si
quieres, vuelve a llamar a `prepare` después para confirmar que quedó al día.
Si la pestaña no tiene compromisos, ofrece el paso 6.

## Output

| Item | Destination |
|------|-------------|
| Referencia a su pestaña (archivo + nombre de pestaña) | `.escala/my-company/tracker.yaml` |
| Su pestaña leída (sólo en la conversación) | `sheet` del módulo; no se guarda |
| Filas propuestas + bloque para pegar | `proposal` (o `rock_proposal` para Rocks) / `paste_block` del módulo; las pega el empresario |
| Preparación de la reunión + bloque para Done | `prep` / `paste_block` del módulo; nada se mueve sin él |
