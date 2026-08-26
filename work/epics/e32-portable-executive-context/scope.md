# Epic Scope: E32 — Contexto Ejecutivo Portátil

**Status:** Complete
**Dependencies:** E21, E22, E23, E26, E28, E29, E30, E31
**Tamaño:** XL

## Outcome

Una persona no técnica puede compartir un archivo desde el host que usa, decidir
qué campos conservar y ver que esos datos confirmados acompañan a su empresa en
la carpeta compartida, los paneles y una consulta al Board. Otro colaborador
que abra la misma carpeta reconstruye el mismo contexto útil local sin recibir
archivos crudos, secretos, historial de chat ni preferencias personales.

## In scope

- Contrato `AttachmentEnvelope` provisto explícitamente por el host: nombre,
  tipo, bytes/ruta temporal efímera, fecha y autorización. La conversación
  nunca pide una ruta ni sintaxis de archivo a la persona.
- Un único pipeline de preview para manual, CSV/XLSX adjunto y contenido que el
  host ya autorizó; se conserva sólo el mínimo de campos aceptados.
- Documento portátil de evidencia confirmada en `areas/{decision}/`, con
  esquema, valor, metodología/campo, fuente minimizada, fecha, vigencia,
  confianza, versión y estado. Sin archivo original, hash reversible, PII,
  tokens ni notas personales.
- Exportación consentida a contribución append-only y reconciliación canónica
  compatible con E26; importación/reconstrucción idempotente de esos documentos
  a SQLite local, incluida sustitución de fuente e historial.
- `CompanyContext` de lectura mínima que compone: perfil/diagnóstico confirmado,
  OPSP, Pulse, evidencia metodológica, prioridades/cadencia y resumen seguro de
  Accountability. Cada hecho conserva procedencia/fecha/estado o se declara
  pendiente.
- Board y Business Pulse consumen `CompanyContext`; el Board recibe sólo la
  proyección humana `board` que ya tenga consentimiento explícito, y registra
  el acceso.
- Paneles muestran evidencia confirmada, vencida o pendiente; no calculan un
  resultado empresarial con datos parciales o vencidos.
- Migración desde bases E22–E31 sin borrar filas; pruebas E2E en instalación
  limpia de Claude, Codex y Hermes.

## Out of scope

- OAuth, instalación de MCPs, lectura de una cuenta o carpeta, sincronización
  propia, scraping, subida a nube o escritura en una fuente externa.
- Compartir SQLite/WAL/SHM/backups, transcriptos, adjuntos originales o
  contexto humano personal.
- Exponer notas personales de Accountability al Board o inferir salud,
  personalidad, desempeño individual o permisos.
- Reemplazar al CRM, sistema contable, contador o proveedor de archivos.

## Reglas no negociables

1. El host entrega un adjunto sólo tras autorización de la persona; ScaleUp no
   descubre archivos ni interpreta una carpeta como autorización.
2. Preview y confirmación por campo preceden toda persistencia portable. Un
   rechazo no conserva el valor crudo.
3. El workspace recibe documentos legibles y mínimos; SQLite continúa local por
   computadora y se puede reconstruir desde esos documentos.
4. Todo consumidor ejecutivo muestra fuente, fecha, vigencia y huecos; no une
   evidencia de distinto dueño/fecha como si fuera una verdad actual.
5. El Board usa datos empresariales confirmados y proyección humana mínima;
   cuando falte algo, lo nombra como hueco y no lo inventa.

## Acceptance criteria

- [x] En Claude, Codex y Hermes una persona adjunta CSV/XLSX sin indicar rutas,
  JSON ni comandos; se ve el mismo preview seguro de E31 y puede volver a
  captura manual.
- [x] Ningún adjunto, bytes, secreto, PII ni valor rechazado queda en SQLite,
  workspace, índice, panel, Board o logs de ScaleUp.
- [x] Cada valor confirmado puede exportarse explícitamente a un documento
  portable y otro equipo reconstruye el mismo snapshot, procedencia, estado y
  versión local sin compartir una base SQLite.
- [x] La sustitución de una fuente conserva historia y actualiza el documento
  canónico/panel sólo tras reconciliación confirmada.
- [x] Business Pulse muestra los datos y huecos del `CompanyContext`; Cash no
  calcula impactos cuando la evidencia necesaria falta o está vencida.
- [x] Una consulta al Board después de Welcome usa perfil, plan y evidencia
  confirmada disponibles; distingue hechos, conocimiento metodológico e
  inferencias, y puede funcionar con huecos.
- [x] El Board recibe únicamente la proyección humana autorizada para `board`;
  no consume ni revela texto personal de Accountability.
- [x] Migración, conflicto de colaboración, host sin adjuntos/MCP y las tres
  instalaciones públicas tienen pruebas reproducibles y gates RaiSE verdes.
