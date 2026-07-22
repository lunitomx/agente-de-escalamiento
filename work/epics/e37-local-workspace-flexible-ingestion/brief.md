---
epic_id: "E37"
title: "Local Workspace & Flexible Ingestion"
status: "complete"
created: "2026-07-22"
mission: "escala-local-v2-plan-maestro-2607202112"
---

# Epic Brief: E37 — Local Workspace & Flexible Ingestion

## Hypothesis

Si el empresario puede instalar el producto en su propia máquina, elegir una
carpeta local de intercambio y entregar sus archivos tal como ya los usa, el
agente podrá comenzar un diagnóstico basado en evidencia sin imponerle una
plantilla ni mover sus datos a un servicio hospedado. La confianza depende de
que la autoridad de datos permanezca local, que cada importación sea repetible
y que las ambigüedades o fallos se hagan visibles antes de afectar el estado
canónico.

## Success Metrics

- **Leading:** los límites de autoridad local, rechazo de SQLite sincronizado,
  formatos admitidos, inferencia de estructura, identidad de fuentes e inbox
  idempotente tienen contratos ejecutables y pruebas positivas/negativas.
- **Lagging:** un flujo real de archivos de una empresa sintética procesa
  entradas válidas desde una carpeta local o sincronizada, vuelve a ejecutarse
  sin duplicar datos, y aísla entradas corruptas, ambiguas o no soportadas sin
  filtrar rutas de la máquina.

## Appetite

M — 3 historias. Es un walking skeleton funcional del límite local y de la
entrada de datos; no reconstruye todavía finanzas, reuniones, cockpit ni
instalación multiplataforma completa.

## Scope Boundaries

### In (MUST)

- Definir raíz local de trabajo, autoridad de runtime y autoridad de datos del
  instalador.
- Rechazar configuraciones donde SQLite o el estado canónico queden dentro de
  una carpeta sincronizada o compartida.
- Aceptar hojas de cálculo, texto delimitado, documentos, PDF y transcripciones
  declarados por el usuario, conservando un resultado explícito para variantes
  no soportadas.
- Inferir hojas, tablas, encabezados, unidades, fechas y entidades candidatas;
  formular preguntas cuando una ambigüedad pueda cambiar la interpretación.
- Registrar fingerprint local, procedencia relativa, estado de extracción e
  identidad repetible sin exponer rutas absolutas.
- Operar una bandeja de entrada idempotente sobre una carpeta elegida por el
  usuario, incluyendo carpetas locales sincronizadas por Drive u OneDrive sin
  APIs, OAuth ni servicio remoto del producto.
- Poner en cuarentena o reportar entradas corruptas, cifradas, demasiado
  grandes, duplicadas o no soportadas sin dañar el estado canónico.

### Should

- Proporcionar recibos JSON/Markdown legibles para cada corrida y una vista de
  pendientes que el agente pueda usar en la sesión diaria.
- Dejar seams claros para que E38-E40 consuman fuentes ya identificadas sin
  volver a implementar la detección de archivos.

### No-Gos

- No alojar runtime, base de datos, transcripciones ni estado de empresa en
  servidores o bases de datos cloud.
- No integrar Google Drive, OneDrive, OAuth, webhooks o APIs de sincronización;
  solo operaciones de sistema de archivos sobre una carpeta ya sincronizada.
- No colocar SQLite autoritativo ni la raíz de datos dentro de esa carpeta.
- No exigir que el usuario convierta sus excels, documentos o transcripts a un
  formato propio antes de entregarlos.
- No interpretar cifras financieras ni emitir el cockpit final; eso pertenece a
  E38 y E40.
- No borrar automáticamente archivos del usuario ni modificar la carpeta
  compartida de forma irreversible.

### Rabbit Holes

- Construir un parser universal que pretenda entender cualquier archivo sin
  declarar límites.
- Añadir OCR, embeddings o un catálogo cloud antes de probar la frontera local
  y las preguntas de ambigüedad.
- Sincronizar la base SQLite para "facilitar" al equipo la colaboración.
- Mezclar reglas contables, coaching o scoring visual en el ingestador.
