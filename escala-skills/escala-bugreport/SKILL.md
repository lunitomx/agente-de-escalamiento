---
description: 'Recibe un reporte anónimo de bug o mejora y genera un archivo local listo para compartir manualmente.'
license: MIT
metadata:
  raise.fase: '0'
  raise.frequency: on-demand
  raise.next: developer-intake
  raise.prerequisites: escala instalado localmente
  raise.version: 1.0.0
  raise.visibility: public
  raise.work_cycle: utility
name: escala-bugreport
---

# Reporte anónimo de bug o mejora

## Purpose

Permitir que una persona reporte un fallo o proponga una mejora sin que Escala
lea la memoria de la empresa, archivos del equipo o datos de identidad. El
resultado es un JSON local, redacted y listo para copiar manualmente a una
carpeta de Google Drive u OneDrive que el equipo haya elegido.

## Mastery Levels (ShuHaRi)

- **Shu**: seguir los pasos y mostrar el preview antes de guardar.
- **Ha**: agrupar reportes similares sólo si la persona lo pide.
- **Ri**: no aplica; la anonimización es una frontera fija, no configurable.

## Context

**Activación:** la frase "quiero reportar un bug/mejora", "reportar problema"
(la que ESCALA sugiere cuando algo falla) o algo parecido.
Es el procedimiento interno `escala-bugreport`; no se presenta al dueño como
comando ni se le pide escribirlo.

**No leer ni recolectar:** `~/.escala/memoria/`, `.escala/my-company/`,
transcripts, hojas de cálculo, adjuntos, variables de entorno, rutas
absolutas, nombre de usuario, empresa, correo, teléfono, hostname, IP,
remotos Git, tokens, cookies, navegador o cualquier otro contexto automático.
No llamar APIs, MCP, GitHub, Jira, correo ni endpoints HTTP.

**Anonimato:** el contenido del payload no lleva identidad. Los metadatos de la
carpeta sincronizada (cuenta, propietario o fecha) dependen de Google Drive o
OneDrive y no pueden prometer anonimato frente a esos servicios.

## Steps

### Step 1: Classify

Preguntar si es `bug` (algo no funciona) o `improvement` (algo podría funcionar
mejor), y pedir un título corto sin nombres propios ni datos de la empresa.

### Step 2: Collect only typed facts

Pedir, uno por uno y sin abrir archivos:

1. Qué ocurrió u observó.
2. Qué esperaba que ocurriera.
3. Pasos mínimos para reproducirlo, si existen.
4. Área afectada: `skill`, `workflow`, `visual`, `installation` u `other`.
5. Severidad: `low`, `medium`, `high` o `blocking`.

La versión, sistema operativo o plataforma sólo se incluyen si la persona los
escribe deliberadamente; nunca se detectan automáticamente.

### Step 3: Redact and validate

Antes del preview, sustituir nombres de personas/empresas, correos, teléfonos,
URLs, rutas, IDs, números de cuenta, importes sensibles, secretos y texto de
archivos por `[redacted]`. Si el reporte depende de un archivo, describir el
tipo de dato sin adjuntarlo. Si no se puede redactar con seguridad, detenerse
y pedir una descripción genérica.

### Step 4: Preview and consent

Mostrar el documento completo que se va a guardar y explicar: "Sólo se
guardará este texto en tu computadora; no se enviará por internet". Guardar
únicamente si la persona responde afirmativamente de forma explícita.

### Step 5: Write local outbox

Crear un identificador aleatorio local no vinculante y guardar un archivo
`~/.escala/feedback/outbox/<report_id>.json`. Si esa carpeta no existe, usar
`.escala/feedback/outbox/` en el directorio de trabajo. No sobrescribir un
archivo existente. Ofrecer una copia Markdown sólo si la persona la solicita.

Usar exactamente este contrato mínimo:

```yaml
schema_version: 1
report_id: local-random-id
report_kind: bug|improvement
title: texto redactado
area: skill|workflow|visual|installation|other
severity: low|medium|high|blocking
observed: texto redactado
expected: texto redactado
reproduction_steps: []
product_version: null
platform: null
consent: confirmed
identity: omitted
company_data: omitted
transport: local_outbox_manual_share
```

## Output

| Item | Destination |
|------|-------------|
| Reporte JSON | `~/.escala/feedback/outbox/` |
| Compartir | Copia manual a carpeta sincronizada elegida por el usuario |
| Seguimiento | El equipo de desarrollo importa el JSON como issue interno |

Nunca afirmar que el issue fue enviado: en esta versión sólo quedó exportado
localmente. El equipo puede recoger los archivos compartidos y ejecutar su
flujo interno de bugfix sin conocer la identidad del reportante.

## Quality Checklist

- [ ] La persona confirmó el preview antes de guardar.
- [ ] El JSON contiene sólo información escrita para este reporte.
- [ ] No hay identidad, datos de empresa, secretos, rutas ni adjuntos.
- [ ] `consent` es `confirmed` y `transport` es `local_outbox_manual_share`.
- [ ] El archivo se creó en outbox local y no hubo llamadas de red.
- [ ] La respuesta distingue claramente "guardado" de "enviado".

## References

- Política local-only de ESCALA: README del producto, sección "Operación local".
- Flujo de reparación del equipo: `/rai-bugfix-start` (uso interno; no se carga
  durante el reporte del empresario).
