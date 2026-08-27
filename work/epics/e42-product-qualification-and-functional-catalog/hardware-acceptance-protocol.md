# E42 — Protocolo privado de hardware limpio y aceptación humana

Este protocolo convierte los pendientes externos de E42 en evidencia repetible.
No sustituye el criterio de aceptación maestro ni permite cerrar la épica por
ejecutar un script.

## Alcance

Se requieren dos recorridos reales del paquete exportado: uno en macOS y otro
en Windows. Cada entorno debe ser una máquina física limpia o una VM dedicada
limpia. No se aceptan emulaciones, fixtures ni simulaciones locales como
equivalentes.

El recibo conserva sólo identificadores opacos, hashes y resultados. No incluye
nombres, rutas, documentos empresariales, credenciales ni transcripciones. Debe
permanecer fuera de Git, en almacenamiento privado local.

## Antes de cada recorrido

1. Construir el export público con: uv run python scripts/build_public_export.py
2. Registrar el commit completo y SHA-256 del manifiesto exportado.
3. Confirmar que el entorno no contiene una instalación previa de ESCALA ni
   datos de prueba anteriores.
4. Usar datos ficticios mínimos, sin material empresarial sensible.

## Recorrido obligatorio

En ambos sistemas, documentar en este orden que el único punto de entrada
público, escala, completó:

1. instalación;
2. creación del espacio local;
3. ingreso de documentos;
4. revisión de reuniones;
5. Cash;
6. Strategy;
7. cockpit;
8. acción y seguimiento.

Si un paso falla, se mantiene la reserva, se corrige en una historia separada
y se repite el recorrido completo.

## Revisión humana y validación

Una persona responsable revisa el catálogo/PDF contra el inventario público y
confirma por separado REQ-E42-001 a REQ-E42-006. La decisión sólo puede ser
accepted cuando las seis respuestas son verdaderas; de lo contrario es
reservations-open y E42 continúa activa.

Guardar el JSON fuera del repositorio y ejecutar:

    uv run python scripts/check_e42_release_acceptance.py /ruta/privada/e42-receipt.json

El comando devuelve 0 sólo con ambos recorridos limpios, los tres controles de
catálogo y los seis requisitos aceptados. El resultado verde sólo vuelve el
recibo elegible para la revisión maestra: no escribe ProvedProof, no publica
nada y no cambia E42 automáticamente.

## Forma mínima del recibo

- schema_version: 1
- receipt_kind: e42-clean-hardware-and-human-acceptance
- storage: private-local-only
- participant_ref: identificador opaco, no personal
- platform_runs: exactamente un macos y un windows, con commit, hash, ocho pasos
  en orden y resultado pass
- catalog_review: los tres controles en true
- requirement_acceptance: los seis REQ-E42-00X, una vez cada uno
- release_decision: accepted o reservations-open
