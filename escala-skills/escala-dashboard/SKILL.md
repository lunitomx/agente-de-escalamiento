---
description: 'Muestra cómo va la empresa (resumen de avance) o recomienda qué tablero ver: máximo 2 propuestas con la decisión que sirven, la fuente y el periodo de cada dato, y si se pueden armar hoy.'
name: escala-dashboard
---

# Escalamiento Dashboard

## Purpose

Dos caminos, según lo que pidió el dueño:

- **"¿Cómo voy?"** → el resumen de avance (scores actuales, historial de pulsos,
  victorias y áreas de atención). Ver "Resumen de avance".
- **"¿Qué debería ver?", "hazme un tablero", "tablero de mis ventas"** → el
  recomendador de tableros (E84 S84.3). Ver "Tableros".

## Architecture

Este skill es un **adapter delgado**. Toda la lógica vive en Python. No contiene lógica de negocio.

## Step 0: Elegir el camino

| Pedido | Camino |
|--------|--------|
| "cómo voy", "mi avance", "mi progreso" | Resumen de avance |
| tablero, dashboard, gráfica, indicadores (cualquier tema) | Tableros |

Si dudas, ve a Tableros: el recomendador manda al resumen de avance cuando eso
es lo que responde.

## Tableros

### Step T1: Recomendar

```bash
echo '{"action": "recommend", "base_path": ".", "request": "<palabras del dueño>", "asked_this_conversation": false}' | python3 -m coaching.dashboard.boards
```

`asked_this_conversation` es `true` si ya se le preguntó en esta conversación
cómo llega un cliente hasta que compra. Lee `result["recommendation"]["outcome"]`:

| outcome | Qué hacer |
|---------|-----------|
| `existe` | Muestra `message` y lleva al dueño a lo que ya existe (`points_to_existing`): reporte de caja, lista de seguimiento, resumen de avance o investigación. No propongas otro tablero. |
| `pregunta_decision` | Haz una sola pregunta, exactamente: "¿Qué quieres decidir con ese tablero? Por ejemplo: en qué paso se te van los clientes, o si tu equipo puede con lo que tiene." Con su respuesta, vuelve a T1 con `"decision": "<respuesta>"` y `"decision_asked": true`. |
| `propuestas` | Muestra `message` tal cual: máximo 2 tableros, cada uno con la decisión que sirve, quién lo mira, cada cuánto, sus datos con fuente y periodo, y si se puede hoy. Termina en la decisión del dueño. |
| `sin_patron` | Muestra `message`. No inventes un tablero. |
| `pospuesto` | Muestra `message`. No insistas. |

Si `journey_question` viene lleno, **no** lo juntes con las propuestas: es una
pregunta aparte. Hazla sólo después de que el dueño decida sobre el tablero, y
registra su respuesta con el procedimiento de cómo llega un cliente hasta que
compra. Así hay una sola pregunta por mensaje.

### Step T2: Guardar la decisión del dueño

Sólo cuando el dueño contesta (sí / todavía no / no):

```bash
echo '{"action": "decide", "base_path": ".", "board_id": "<board_id>", "outcome": "construir|esperar|no", "review_on": "AAAA-MM-DD"}' | python3 -m coaching.dashboard.boards
```

- `review_on` sólo con `esperar`, y es la fecha que dio el dueño (pregúntala si
  no la dio). Nunca la inventes.
- Se guarda en `.escala/my-company/tableros/index.yaml`, sólo con códigos; nunca
  las palabras del dueño. Un tablero con "todavía no" o "no" no se vuelve a
  proponer en 30 días.
- Muestra `message`.

### Step T3: Armar el tablero aceptado

Sólo después de un «sí» del dueño (T2 con `construir`):

```bash
echo '{"action": "generate", "base_path": ".", "board_id": "<board_id>"}' | python3 -m coaching.dashboard.boards
```

- Toma los números de los datos locales y del recorrido del cliente guardado;
  cada número lleva su fuente y su mes. Nada se estima.
- Con `saved_files`: el tablero quedó en `.escala/my-company/tableros/` (un
  HTML que se abre en el navegador, también en el teléfono, y su gemelo `.md`).
  Muestra `markdown` en el chat y luego `message`.
- Con `saved_files` vacío: no había ni un número; no se armó nada. Muestra
  `message` (dice qué datos conseguir). Es el «todavía no».
- `errors: ["not_accepted"]`: el dueño no ha dicho que sí; vuelve a T2.
- Si no puedes correr Python o escribir archivos, arma el tablero sólo en el
  chat con los datos que el dueño te dé (los que falten, «Falta») y di
  claramente que no se guardó ningún archivo.

### Reglas de Tableros

- Nunca inventes cifras: un dato que falta se dice "falta".
- Nunca publiques un tablero (artifacts, canvas, enlaces compartidos ni nada
  parecido). Los tableros sólo viven en la computadora del dueño.
- No muestres nombres de procedimientos ni comandos al dueño.
- Sólo se arma el tablero que el dueño aceptó; nunca uno que dijo «todavía no»
  o «no».

## Resumen de avance

### Step 1: Prerequisite Check

```bash
test -f .escala/agent/memory/company-profile.yaml && echo "EXISTS" || echo "NO_PROFILE"
```

| Result | Action |
|--------|--------|
| NO_PROFILE | Ofrece empezar desde el inicio: la empresa todavía no tiene perfil |
| EXISTS | Continue |

### Step 2: Invoke Core Module

```bash
echo '{"base_path": "."}' | python3 -m coaching.dashboard
```

Capture the JSON result. The dashboard output is in `result["output"]`.

### Step 3: Quality Gate

Save the dashboard output to a temp file and validate:

```bash
echo '{"base_path": "."}' | python3 -m coaching.dashboard | python3 -c "
import sys, json
result = json.loads(sys.stdin.read())
with open('/tmp/dashboard-output.md', 'w') as f:
    f.write(result['output'])
print(json.dumps(result, indent=2, ensure_ascii=False))
" > /tmp/dashboard-result.json && python3 .escala/agent/validators/dashboard.py /tmp/dashboard-output.md
```

Exit 0 = validation passed. Exit 1 = missing sections (show errors).

### Step 4: Present Dashboard

- La salida del módulo todavía está en inglés y menciona comandos (lo corrige
  E80). **No la muestres cruda: resúmela en español**, sin comandos.
- If `result["errors"]` is non-empty, explica en español qué falta.
- If `artifacts["pulse_count"]` is 0, ofrece empezar a registrar cómo va cada
  semana, sin mencionar comandos.

### Step 5: Handle Errors

If `result["errors"]` is non-empty:
1. Explica cada error en español llano
2. Ofrece el siguiente paso (diagnóstico o registro semanal) sin mencionar comandos

## Output Sections

| Section | Data Source | Behavior When Empty |
|---------|-------------|---------------------|
| Current Scores | `company-profile.yaml` → `scores` | "No diagnosis yet. Run /escala-diagnose first." |
| Pulse History | `pulse-history.yaml` → `pulses` | "No pulse data yet. Run /escala-pulse to start tracking." |
| Wins | Last pulse `trends` where improving | "No improving trends in the latest pulse." |
| Attention Areas | Last pulse `trends` where regressing or 2+ stalling | "No attention areas detected. Keep up the momentum!" |
