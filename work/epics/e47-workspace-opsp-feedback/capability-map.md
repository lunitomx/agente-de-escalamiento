# E47 — Mapa de capacidades previo al diseño

## Parte 1 — Hallazgos de Gemba

| Dominio | Capacidad existente | Estado | Disposición |
|---|---|---|---|
| Workspace Codex | `.mcp.json` declara `rai-mcp-pipeline`; `.codex/config.toml` local registra el servidor completo. | Parcial: el archivo rastreado usa un comando bare y el provisionador deja drift. | Extender. |
| Instalación | `install.sh` crea symlinks globales y paquete editable; `escala_server.lifecycle.installer` genera bundle local. | Parcial: recursos de skills no se materializan junto al runtime. | Extender. |
| OPSP | Skill conversacional, `WorksheetDAO` versionado y estrategia parcial en executive. | Parcial: rutas no instaladas, estructura incompleta y sin renderer. | Extender. |
| Feedback | Skill local-only y pruebas de contrato. | Parcial: JSON, no toma contexto visible y no produce Markdown. | Extender. |

No se encontró una implementación que deba reescribirse completa. Las coincidencias del grafo provenientes de otros repositorios se excluyeron: no son evidencia de capacidad instalada en ESCALA.

## Parte 2 — Escaneo de backlog

Consultas ejecutadas contra `ESCALA`:

| Consulta | Resultado | Decisión |
|---|---|---|
| `summary ~ "OPSP"` | `ESCALA-1`, `ESCALA-2` | No existe trabajo activo duplicado. |
| `summary ~ "workspace"` | `ESCALA-1` | E47 es el único trabajo activo del dominio. |
| `summary ~ "feedback"` | `ESCALA-1` | E47 concentra el cambio; feedback no se duplica. |

Jira se validó mediante la cuenta Eduardo Luna. El Epic es `ESCALA-1` y la primera historia es `ESCALA-2`.

## Parte 3 — Validación del alcance

- S47.1 extiende el contrato de workspace y agrega pruebas de provisión limpia; no mueve secretos ni cambia la base global de RaiSE.
- S47.2 reutiliza las rutas de instalación existentes y migra recursos de forma idempotente.
- S47.3 y S47.4 reutilizan el DAO de worksheets en lugar de introducir otra base de datos.
- S47.5 endurece el feedback existente; no crea red, telemetría ni una integración automática de Jira.
- S47.6 verifica recorridos y límites; la aceptación humana sigue siendo una decisión externa.

**Resultado:** alcance suficiente. Cuatro capacidades se extienden; no hay duplicación activa en Jira ni razón para un subsistema nuevo.
