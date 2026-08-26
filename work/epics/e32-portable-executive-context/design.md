# Diseño: E32 — Contexto Ejecutivo Portátil

## Flujo único

```text
Adjunto explícito / dato manual / contenido autorizado
                        ↓
             Preview + clasificación local
                        ↓
        Confirmación individual de cada campo
                        ↓
  SQLite local ←→ contribución portable confirmada
                        ↓
         reconstrucción idempotente en otro equipo
                        ↓
 CompanyContext (hechos + fuente + fecha + vigencia + hueco)
            ├── Business Pulse / paneles
            └── Board sintético con proyección humana opt-in
```

## Fronteras

`AttachmentEnvelope` es un adaptador del runtime instalado, no un conector.
Sólo acepta un adjunto que el host ya entregó para este turno. Después del
preview el payload se descarta; el contrato de evidencia actual sigue siendo la
única puerta para valores persistentes.

Los documentos portables no son un dump de SQLite. Contienen únicamente los
campos aceptados, con una fuente minimizada y la fecha observada. El índice E26
los trata como contribuciones/canónicos normales; el importador E32 los
convierte otra vez en filas locales sin cambiar su significado.

`CompanyContext` es de lectura: no actualiza plan, evidencia ni Accountability.
Compone hechos con IDs de procedencia, descarta/vuelve visible lo vencido y
entrega una proyección distinta por consumidor (`pulse`, `board`). El Board
recibe hechos de empresa y, sólo si existe consentimiento, preferencias de
colaboración para el consumidor `board`.

## Decisiones de migración

- Las tablas E31 se mantienen; se añade un export/import idempotente y una
  referencia reversible entre fila local y documento portable.
- Un documento compartido nunca contiene el hash de un archivo fuente ni su
  ubicación local. Conserva una etiqueta de fuente aprobada por la persona.
- La reconciliación E26 es el único lugar que promueve una contribución a
  canónico; no hay “last write wins”.
