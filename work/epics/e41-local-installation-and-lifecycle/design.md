# E41 Design — Local Installation and Lifecycle

## Decisions

1. `escala_server.lifecycle` es un paquete tipado, cerrado con Pydantic, que
   trata el instalador como la autoridad de runtime y datos.
2. El paquete distribuible es un ZIP determinista de `escala_server` solamente;
   no incluye `.git`, `work/`, tests ni la disposición de desarrollo.
3. La instalación valida `WorkspaceConfig` antes de crear SQLite o escribir
   configuración. Un exchange opcional se valida como documentos ordinarios.
4. El runtime local usa un marcador de salud y CLI local; no inicia workers
   hospedados, OAuth, APIs cloud ni acciones de red.
5. Actualizaciones requieren hash exacto y commit de procedencia; cada
   migración/update crea un ZIP recuperable antes de activar la nueva versión.
6. Scheduling se expresa como `launchd` o Windows Task Scheduler, con paths
   redacted y `network_required=false`.

## Evidence

- Implementation: `escala_server/lifecycle/`
- Focused tests: `tests/test_e41_lifecycle.py`, `tests/test_e41_gates.py`
- Qualification: `scripts/qualify_e41.py`
- Gates: `validators/e41_gates.py`
