# E26 — Plan de ejecución

## Orden recomendado

1. **S26.1 — Contrato compartido/local.** Congelar arquitectura, manifest y
   formatos antes de tocar persistencia.
2. **S26.2 — SQLite local por workspace.** Separar raíces y migrar E22.
3. **S26.3 — Documentos y contribuciones.** Crear esquemas y validadores.
4. **S26.4 — Scanner y reconstrucción.** Indexación incremental y rebuild.
5. **S26.5 — Colaboradores y conflictos.** Propiedad, propuestas y conciliación.
6. **S26.6 — Experiencia y release.** Welcome, Doctor, E2E y guía no técnica.

## Gates

- **Gate A:** contrato aprobado; ninguna ruta ambigua permite DB compartida.
- **Gate B:** migración reversible con respaldo y suite E22 verde.
- **Gate C:** digest determinístico en dos estados locales independientes.
- **Gate D:** prueba real con carpeta sincronizada, offline/reconexión y copia en
  conflicto, sin pérdida de información.
- **Gate E:** smoke conversacional desde instalación limpia en Claude y Codex.

## Definición de terminado

Las seis stories están cerradas con pruebas y evidencia; una persona no técnica
puede seleccionar/crear la carpeta, compartirla mediante su proveedor habitual,
incorporar otro colaborador y entender cualquier conflicto sin operar SQLite.
