# E41: instalación local y lifecycle

## Flujo soportado

1. Obtener el ZIP de la plataforma (`escala-local-macos-<version>.zip` o
   `escala-local-windows-<version>.zip`) en la máquina del instalador.
2. Extraerlo en una carpeta local y ejecutar el flujo de `install.sh` o
   `install.ps1` con Python local disponible.
3. Configurar `install_root`, `data_root`, `database_path` y, opcionalmente,
   una carpeta de intercambio de documentos de Google Drive, OneDrive o red.
4. Verificar estado con `python -m escala_server.lifecycle status ...`.

El ZIP lifecycle probado aquí instala sólo el runtime local. No equivale todavía
al paquete conversacional completo de ESCALA: la reparación S10.10 de E10 debe
empaquetar skills, catálogo, conocimiento permitido y adaptadores sin depender
del checkout fuente. SQLite, configuración, runtime marker y backups permanecen
en `data_root`. La carpeta sincronizada no contiene autoridad ni SQLite; solo
recibe/entrega documentos ordinarios.

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
