# Diseño: E31 — Evidencia Operativa a Metodologías

## Decisión de experiencia

El diagnóstico de E27 responde “dónde duele y por qué”; E31 responde “qué dato
mínimo hace falta para decidir y cómo lo obtenemos”. No cambia el score en
automático ni obliga a que haya score.

```text
Relato / foco confirmado
        ↓
¿Mantener cualitativo o cuantificar ahora?
        ↓
Manual ─ Archivo local ─ MCP ya autorizado por el host
        ↓
Preview de columnas/campos + alerta de sensibilidad
        ↓
Persona confirma, corrige o descarta cada campo
        ↓
Metodología y panel con fuente, fecha y dato pendiente
```

## Modelo de evidencia

- `evidence_sources`: identidad local, tipo (`manual`, `file_preview`,
  `host_connector`), fecha observada, alcance permitido y hash opcional.
- `evidence_proposals`: valor propuesto, campo destino, transformaciones,
  sensibilidad y estado (`proposed`, `accepted`, `rejected`, `superseded`).
- `methodology_values`: valor confirmado, metodología/campo, fuente, fecha,
  versión y vigencia.

El archivo bruto no es la base de conocimiento. Por defecto se procesa en la
sesión local para crear propuestas; sólo los valores aceptados se conservan.

## Ruta Cash inicial

Antes de pedir un archivo, se explica el modelo y se pregunta qué fuente tiene
la persona. Si elige Power of One, se solicitan o mapean: precio, volumen,
COGS, gastos operativos, días A/R, días de inventario y días A/P. Si falta una
variable, la visual muestra su estado pendiente, nunca 0 como resultado.

## Frontera MCP

ScaleUp detecta capacidades declaradas por el host. El usuario decide abrir el
conector y compartir contenido. Cuando el host devuelve contenido, E31 lo
trata como una fuente temporal con el mismo preview y consentimiento que un
archivo. No presupone acceso continuo ni escribe en la fuente externa.

## Privacidad y colaboración

La misma política aplica a archivo, conversación y MCP. Secretos, cuentas,
identificadores y PII se bloquean/minimizan antes de crear una propuesta. La
evidencia aceptada vive en SQLite local; un workspace compartido recibe sólo
documentos explícitamente confirmados y nunca SQLite/WAL/archivos fuente.
