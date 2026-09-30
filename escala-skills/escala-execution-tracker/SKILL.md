---
description: 'Encuentra la pestaña propia del empresario en la hoja compartida de su grupo de accountability, con su confirmación, sin mirar las de los demás.'
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

Si el empresario prefiere pegar su pestaña, salta al paso 5 con `pasted_text`
(si no sabes cómo se llama su pestaña, pregunta: "¿Cómo se llama tu pestaña en
la hoja? Casi siempre es tu nombre.").

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

### Paso 6: Siguiente paso

Con su pestaña confirmada, ofrece el siguiente paso (proponer filas para sus
compromisos del mes) sin mover nada todavía.

## Output

| Item | Destination |
|------|-------------|
| Referencia a su pestaña (archivo + nombre de pestaña) | `.escala/my-company/tracker.yaml` |
| Su pestaña leída (sólo en la conversación) | `sheet` del módulo; no se guarda |
