# E41: instalación local y lifecycle

## Cómo se instala hoy

El dueño instala con una sola línea, la del `README.md` (`instalar.sh`): clona el
repo público a `~/ESCALA` y corre `install.sh --platform claude --with-specialists`.
Actualiza con la misma línea.

El paquete por plataforma de E41 se quitó en S86.35: nadie lo usaba. De E41
queda `prepare_local_install`, que prepara `install_root`, `data_root`, la base
SQLite y, opcionalmente, una carpeta de intercambio de documentos de Google
Drive, OneDrive o red. SQLite, configuración, marcador de versión y respaldos
permanecen en `data_root`. La carpeta sincronizada no contiene autoridad ni
SQLite; solo recibe y entrega documentos ordinarios. El estado se consulta con
`python -m escala_server.lifecycle status ...`.

## Actualizaciones y rollback

Un artefacto debe tener hash SHA-256 y commit de procedencia. `verify_update_artifact`
debe pasar antes de `UpdateManager.apply`. Cada activación crea un backup local;
`UpdateManager.rollback` restaura la versión anterior. Una migración interrumpida
devuelve `safe_stop` y conserva el backup.

## Scheduling

`build_native_schedule` genera `launchd` en macOS y Windows Task Scheduler en
Windows. Ambos declaran `network_required=false` y ejecutan el módulo local.

## Verificación de esta épica

```text
uv run python scripts/qualify_e41.py
uv run pytest tests/test_e41_lifecycle.py tests/test_e41_gates.py -q
```

La aceptación en una máquina Windows física, firma/notarización y publicación
requieren una decisión posterior de producto y legal; no se inventan aquí.
