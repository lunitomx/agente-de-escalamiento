# Cartera de épicas — auditoría de verdad 2026-08-27

## Resultado de la auditoría

La auditoría revisó scopes, briefs, retrospectivas, GitHub, recibos de
aceptación y los gates locales. La aceptación maestra de E37–E42 ahora tiene
**36 requisitos demostrados de 42**. Los seis faltantes pertenecen a E42; no
se alteraron para aparentar cierre.

| Hallazgo | Disposición | Acción registrada |
|---|---|---|
| E42 estaba `complete` aunque sus seis requisitos no tenían prueba maestra vigente. | `active` | Scope y brief corregidos; conserva evidencia histórica, pero exige hardware/skills/aceptación reales. |
| E43 tenía documentación contradictoria. | `complete` (gate E42 para release) | Se verificaron las seis historias, el cierre histórico y 135 pruebas focalizadas actuales. |
| E47 decía `done` y `started` a la vez; RaiSE no era una dependencia de producto. | Reparado; `complete` | Calificación fresca de workspace/OPSP/feedback pasa; la deuda de RaiSE queda aislada en E76. |
| El backlog raíz seguía apuntando al repositorio viejo y a E1–E5 como plan actual. | Reemplazado | `governance/backlog.md` es la fuente única de trabajo futuro. |
| Un remoto local `legacy-scaleupagent` contrariaba la política de un único canónico. | Reparado | Retirado sólo de la configuración local; `origin/main` vuelve a sincronizado. |
| RaiSE no tenía manifest/configuración/grafo de proyecto reproducibles. | E76 completada | Se restauró el contrato mínimo sin venv duplicado; los warnings opcionales quedan documentados, no se fuerzan con infraestructura. |

### Disposición de identificadores no asignados

- **E66:** no existe como épica formal: la auditoría 2026-08-27 no encontró
  scope, brief, entrada de backlog ni historial Git asociado. Se registra como
  **no asignada/reservada**, no como trabajo pendiente ni cierre implícito.
  Sólo podrá reutilizarse mediante un scope nuevo que indique objetivo,
  dependencias, criterios de terminación y su relación con este registro.

## Estados canónicos

### Estados actuales

| Épica | Estado | Próxima decisión verificable |
|---|---|---|
| E10 | active | S10.10 reparó el bundle portable local; E42/E68 aún deben confirmar hardware limpio y modelos reales. |
| E42 | active | Calificar producto en plataformas limpias y registrar aceptación humana, usando el artefacto portable reparado por E10. |
| E44 | in_progress | Ejecutar retrospectiva y aceptación de empresario; la calificación técnica local ya cubre los cuatro pilares sin reclamar causalidad. |
| E45 | in_progress | Comparar contra un coach único en piloto empresarial; el router y las rutas de seguridad ya están calificados localmente. |
| E60 | in_progress | Completar inspección visual autorizada de OPPP/FACe/PACe; la semántica y la cobertura privada ya fueron revisadas. |
| E61 | in_progress | Completar inspección visual autorizada de SWT, Seven Strata, OPSP y Vision Summary. |
| E62 | in_progress | Completar inspección visual autorizada de WWW/checklist/agendas; no hay distorsión técnica crítica abierta. |
| E63 | in_progress | Mantener CASh source-bounded y completar la revisión independiente de candidatos con evidencia autorizada. |
| E76 | complete | Contrato RaiSE mínimo, grafo y retrospectiva ya son reproducibles; los warnings opcionales no pertenecen al producto. |

### Completas verificadas

- E47: workspace, OPSP y feedback local re-verificados; RaiSE reproducible se resolvió en E76.
- E49: diagnóstico/evidencia, ruta de 90 días y recibo local re-verificados.
- E52: persistencia y reanudación local consentida de Welcome re-verificadas.
- E55: GitHub #9 resuelto: onboarding multifuente, conciliación y calificación local verificable.
- E56: catálogo canónico y una sola puerta pública re-verificados.
- E57, E58 y E59: cadena de fuente privada, migración ontológica y fundamentos fieles cerrados con evidencia y validadores.

### Planificado, con dependencias explícitas

E46, E64–E75 y E67–E70 permanecen planificados según el orden de
`backlog.md`. No son deuda olvidada: su alcance existe, pero no se marcan como
entregados por contener documentos de diseño. E64 espera que E60–E63 cierren
sus gates de fuente; E46 espera resultados reales de E44/E45.

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
