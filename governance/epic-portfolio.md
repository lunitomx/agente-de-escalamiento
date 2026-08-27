# Cartera de épicas — auditoría de verdad 2026-08-27

## Resultado de la auditoría

La auditoría revisó scopes, briefs, retrospectivas, GitHub, recibos de
aceptación y los gates locales. La aceptación maestra de E37–E42 ahora tiene
**36 requisitos demostrados de 42**. Los seis faltantes pertenecen a E42; no
se alteraron para aparentar cierre.

| Hallazgo | Disposición | Acción registrada |
|---|---|---|
| E42 estaba `complete` aunque sus seis requisitos no tenían prueba maestra vigente. | `active` | Scope y brief corregidos; conserva evidencia histórica, pero exige hardware/skills/aceptación reales. |
| E43 decía `done` en scope y `planned` en brief sin evidencia de cierre. | `planned` | Todas las historias vuelven a Pending. |
| E47 decía `done` y `started` a la vez; RaiSE no era una dependencia de producto. | Reparado; `complete` | Calificación fresca de workspace/OPSP/feedback pasa; la deuda de RaiSE queda aislada en E76. |
| El backlog raíz seguía apuntando al repositorio viejo y a E1–E5 como plan actual. | Reemplazado | `governance/backlog.md` es la fuente única de trabajo futuro. |
| Un remoto local `legacy-scaleupagent` contrariaba la política de un único canónico. | Reparado | Retirado sólo de la configuración local; `origin/main` vuelve a sincronizado. |
| RaiSE no tiene manifest/configuración/grafo de proyecto reproducibles. | E76 activo | Se separa de funcionalidades de negocio y no se resuelve creando venvs duplicados. |

## Estados canónicos

### Activos o revisables

| Épica | Estado | Próxima decisión verificable |
|---|---|---|
| E42 | active | Calificar producto en plataformas limpias y registrar aceptación humana. |
| E52 | complete | Persistencia y reanudación local consentida de Welcome re-verificadas. |
| E56 | complete | Catálogo canónico y una sola puerta pública publicados y re-verificados. |
| E47 | complete | Workspace, OPSP y feedback re-verificados; RaiSE reproducible es deuda separada de E76. |
| E49 | complete | Diagnóstico/evidencia, ruta de 90 días y recibo local re-verificados. |
| E55 | complete | GitHub #9 resuelto: onboarding multifuente, conciliación y calificación local verificable. |
| E76 | active | Recuperar el contrato mínimo de RaiSE sin tocar datos de empresa ni duplicar entornos. |

### Planificado, con dependencias explícitas

E43–E46, E44–E45, E57–E75 y E67–E70 permanecen planificados según el orden de
`backlog.md`. No son deuda olvidada: son trabajo aún no iniciado y no deben
marcarse como entregados por contener documentos de diseño.

### Legado y disposiciones terminales

- Los IDs de dos dígitos ambiguos se resuelven sólo por
  `governance/epic-identities.yaml`; no se usa `E18`, `E19`, `E20`, `E21` o
  `E22` sin sus cuatro dígitos.
- E1901 sigue `deferred/backlog`; documentos antiguos que lo llaman terminado
  son contexto histórico, no estado vigente.
- Los directorios con sólo stories, sin frontmatter de scope, quedan como
  archivo histórico hasta una migración explícita; no aparecen como pendientes
  activos.
- E54 sólo generó la retrospectiva de E47. No puede cerrar E47 por sí sola; su
  trabajo queda absorbido por la revisión actual de E47.

## Gates ejecutados durante la auditoría

- `uv run pytest`: 1220 passed, 2 skipped, sin warnings.
- `uv run pyright`: 0 errors, 0 warnings tras corregir un defecto real del
  renderer de reuniones.
- `uv run ruff check coaching escala_server validators scripts tests`: pass.
- `check_master_acceptance --mode baseline`: 36 proved / 6 unproved; todos los
  no demostrados son de E42.
- `check_governance_contract`: pass.
- `check_repository_truth`: pass tras retirar el remoto heredado.

## Regla de mantenimiento

Antes de crear una nueva épica, se debe: (1) consultar este registro, (2)
reutilizar o ampliar la épica que ya posea el resultado, y (3) enlazar scope,
PRD, historias, pruebas y disposición. Así se evita que un nuevo archivo
convierta trabajo no formalizado en otra “épica fantasma”.
