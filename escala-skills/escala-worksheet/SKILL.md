---
description: 'Guía paso a paso de las hojas de trabajo de Escalamiento de Negocios: pregunta, cómo llenarla, ejemplo y tips. Al guardar abre una vista clara. Core Python cross-platform.'
name: escala-worksheet
---

# Escalamiento Worksheet

## Purpose

Guiar al dueño por una hoja de trabajo, paso a paso. Cada paso trae la pregunta, cómo llenarla, un ejemplo real y tips con su fuente. Al guardar, el dueño ve su hoja en una página clara.

## Architecture

Lógica en el paquete `coaching.worksheet` (instalado con `install.sh`). Las hojas salen del registro de conocimiento del paquete, o del registro propio del cliente si existe.

Todas las llamadas usan la misma forma: JSON por `stdin` a `run`.

```bash
echo '<JSON>' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from coaching.worksheet import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

## Steps

### Step 1: Listar las hojas

JSON: `{"action": "list", "base_path": "."}`

Muestra la tabla de `output`. Si el dueño ya nombró una hoja, salta al paso 2.

### Step 2: Empezar o reanudar

Usa el `id` de la hoja que aparece en la tabla de `list`. También sirve su nombre en español, con o sin acentos (ej. `"promesa de marca"`).

- Nueva: `{"action": "start", "worksheet_name": "worksheet-core-customer", "base_path": "."}`
- En progreso: `{"action": "resume", "worksheet_name": "worksheet-core-customer", "base_path": "."}`

Muestra `output` tal como viene. En una hoja guiada cada paso trae:

- la pregunta,
- **Cómo llenarlo**,
- **Ejemplo**,
- **Tips**, cada uno con su fuente.

Si `errors` dice que la hoja no cumple el contrato, muéstralo y detente.

El Lienzo de estrategia (`worksheet-strategy-canvas`) lee las hojas guardadas del dueño y no las cambia. Su paso 1 muestra "Esto ya llenaste:" y cada pieza que falta con el comando para llenarla.

### Step 3: Avanzar un paso

Después de cada respuesta del dueño, guárdala con el id del paso:

JSON: `{"action": "step", "worksheet_name": "worksheet-core-customer", "fields": {"quien-es": "Dueños de fondas a 3 km que no pueden quedarse sin tortilla"}, "base_path": "."}`

El primer `step` (después de "listo") no lleva `fields`. Muestra el siguiente paso de `output`.

Después de la última respuesta, `output` trae la **Revisión Final**: cada pregunta con su respuesta y, si la hoja lo tiene, el **Prompt para tu asistente de IA**. La hoja sigue en progreso. Muéstrala completa, con el prompt, y espera:

- Si el dueño quiere cambiar algo, manda un `step` con ese id en `fields`.
- Si responde "confirmar", pasa al paso 4.

### Step 4: Guardar (solo después de "confirmar")

JSON: `{"action": "save", "worksheet_name": "worksheet-core-customer", "base_path": "."}`

Solo `save` marca la hoja como completada. Escribe la vista (`.html` y su gemelo `.md`).

### Step 5: Abrir la vista

Lee `artifacts.view` del resultado de `save`: `{html, md, open_cmd}`.

1. Si `open_cmd` no es `null`, córrelo tal cual. En macOS es `open <ruta.html>`; en Linux es `xdg-open <ruta.html>`. El navegador muestra la hoja.
2. Si `open_cmd` es `null` o el comando falla, muestra en el chat el contenido del `.md` y da su ruta.
3. Publicar el `.html` como artefacto es opcional; lo decide la sesión.

La vista dice "Falta: …" en cada paso sin respuesta, con cómo llenarlo. Así el dueño ve qué le queda.

## Output

| Item | Destino |
|------|---------|
| Respuestas de la hoja | `.escala/my-company/worksheets/<id>.yaml` |
| Vista para el navegador | `.escala/my-company/vistas/AAAA-MM-DD-<id>.html` |
| Gemelo para el chat | `.escala/my-company/vistas/AAAA-MM-DD-<id>.md` |
