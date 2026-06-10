---
description: 'Lee tu organigrama real (Excel, Sheets, PDF, o lo que tengas) y lo mapea al FACe de Scaling Up. Detecta huecos, duplicidades y personas overloaded.'
name: escala-people-organigrama
---

# Escalamiento People — De tu Organigrama al FACe

## Purpose

No me pidas que llenes el FACe a mano. Pásame tu organigrama real — el que ya tienes en Excel, Google Sheets, un PDF, o hasta una foto de tu pizarrón. Yo lo leo, lo mapeo a las funciones del FACe, y te digo qué huecos tienes.

## Steps

### Step 1: Recibir el organigrama

Preguntar al usuario: "¿Dónde está tu organigrama hoy?"

Opciones:
- **Google Sheets / Drive** — "Compárteme el link o conéctame a tu Drive. Si usas Claude Code, ya puedes autorizarme."
- **Excel local** — "Súbelo aquí, yo lo leo."
- **PDF** — "Súbelo, extraigo los nombres y jerarquía."
- **Foto de pizarrón / papel** — "Tómale foto, yo identifico las cajas y reportes."
- **De cabeza** — "Dime los nombres y roles, yo los organizo."

### Step 2: Extraer estructura

Una vez recibido el archivo:

1. Extraer todas las personas: nombre, rol/cargo, a quién reporta
2. Si hay jerarquía explícita (líneas de reporte), respetarla
3. Si no hay jerarquía clara, inferir por nombres de cargo (CEO > VP > Director > Manager)
4. Presentar al usuario la estructura detectada: "Esto es lo que veo. ¿Es correcto?"

### Step 3: Mapear al FACe

Cargar `.escala/knowledge/people/tools/face.md` para la lista de funciones estándar.

Para cada función del FACe:
- ¿Quién la ocupa en el organigrama real? → Asignar nombre
- ¿Está vacía? → Marcar como HUECO
- ¿Una persona ocupa más de 3 funciones? → ALERTA: overloaded
- ¿El CEO ocupa funciones operativas? → ALERTA: founder's trap

### Step 4: Presentar diagnóstico

Mostrar tabla:

| Función FACe | Persona | Estado |
|-------------|---------|--------|
| CEO | Eduardo Muñoz | ✅ |
| VP Ventas | — | 🔴 HUECO |
| VP Marketing | — | 🔴 HUECO |
| VP Operaciones | María García | ✅ |
| Controller | Juan Pérez | ⚠️ También es VP Finanzas |

Alertas adicionales:
- "Juan Pérez tiene 4 funciones. El máximo recomendado es 3."
- "Tienes 2 huecos en posiciones de crecimiento. Sin VP de Ventas, ¿quién está vendiendo?"
- "El CEO está cubriendo funciones operativas. Eso no escala."

### Step 5: Guardar y próximos pasos

Guardar en `work/people/fac-chart.md`.

Preguntar: "¿Quieres que trabajemos en un plan de hiring para cubrir estos huecos?" → sugerir `escala-people-topgrading`.

## Output

- FACe poblado con nombres reales del organigrama
- Lista de huecos con prioridad (crítico / importante / deseable)
- Alertas de overload y founder's trap
- Archivo guardado en `work/people/fac-chart.md`

## Notas

- Este skill NO programa nada. Usa las capacidades nativas de Claude Code/Codex para leer archivos e imágenes.
- Si el usuario no tiene organigrama formal, guiarlo a dibujarlo: "Dime quién reporta a quién. Aunque sean 3 personas. Empecemos por ahí."
