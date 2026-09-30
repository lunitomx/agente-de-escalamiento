# Cartera de épicas — actualización 2026-09-12

## Reparación del piloto

La auditoría del 2026-09-12 demuestra regresiones de instalación, actualización,
aislamiento, scores y health, además de límites de privacidad/ingestión y
calificación. Se registran E78–E81 con 24 historias planificadas y propietario
único por reparación. E41 vuelve a `active` por la regresión reproducida H05;
E78 implementa y E41 recualifica. [Hallazgos y mapa de propiedad](pilot-readiness-2026-09-12.md).

El conteo 36/42 y los resultados del apartado siguiente son históricos de la
auditoría de agosto; no certifican la versión actual ante los nuevos hallazgos.

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
| El remoto heredado legacy-scaleupagent contrariaba la politica de un unico canonico. | Remoto reparado; sincronizacion pendiente | origin sigue siendo el unico remoto permitido. Mientras haya commits locales sin publicar, el gate de sincronizacion debe consultarse en tiempo real; no se corrige mediante cambios de politica ni push automatico. |
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
| E10 | active | E78 repara lanzador/update actuales; E42/E68 aún deben confirmar hardware limpio y modelos reales. |
| E41 | active | Recualificar runtime y lifecycle con las reparaciones E78; un marker no prueba ejecución real. |
| E42 | active | Calificar producto en plataformas limpias y registrar aceptación humana, usando el artefacto portable reparado por E10. |
| E44 | in_progress | Ejecutar retrospectiva y aceptación de empresario; la calificación técnica local ya cubre los cuatro pilares sin reclamar causalidad. |
| E45 | in_progress | Comparar contra un coach único en piloto empresarial; el router y las rutas de seguridad ya están calificados localmente. |
| E60 | in_progress | Completar inspección visual autorizada de OPPP/FACe/PACe; la semántica y la cobertura privada ya fueron revisadas. |
| E61 | in_progress | Completar inspección visual autorizada de SWT, Seven Strata, OPSP y Vision Summary. |
| E62 | in_progress | Completar inspección visual autorizada de WWW/checklist/agendas; no hay distorsión técnica crítica abierta. |
| E63 | in_progress | Mantener CASh source-bounded y completar la revisión independiente de candidatos con evidencia autorizada. |
| E75 | in_progress | S75.1/S75.2 sustituyen el cuestionario 1–5 por assessment narrativo confirmable; los handoffs profundos esperan E65. |
| E76 | complete | Contrato RaiSE mínimo, grafo y retrospectiva ya son reproducibles; los warnings opcionales no pertenecen al producto. |
| E78 | planned | Diseñar S78.1 y probar instalación, ejecución, actualización y recuperación reales. |
| E79 | planned | Diseñar identidad/aislamiento y cerrar la frontera HTTP; migración consume backup E78. |
| E80 | planned | Definir indicadores honestos y reparar intake/continuidad con contexto E79. |
| E81 | planned | Preparar protocolo y soporte; observar humanos sólo tras reparaciones y evidencia aplicable. |

### Completas verificadas

- E47: workspace, OPSP y feedback local re-verificados; RaiSE reproducible se resolvió en E76.
- E49: diagnóstico/evidencia, ruta de 90 días y recibo local re-verificados.
- E51: los cinco residuos de issues se re-verificaron; sus cuatro issues de GitHub están cerrados y la evidencia de cierre está versionada.
- E52: persistencia y reanudación local consentida de Welcome re-verificadas.
- E55: GitHub #9 resuelto: onboarding multifuente, conciliación y calificación local verificable.
- E56: catálogo canónico y una sola puerta pública re-verificados.
- E57, E58 y E59: cadena de fuente privada, migración ontológica y fundamentos fieles cerrados con evidencia y validadores.

### Planificado, con dependencias explícitas

E46, E64–E74, E67–E70, E77–E81 y S75.3–S75.6 permanecen planificados según el orden
de `backlog.md`. No son deuda olvidada: su alcance existe, pero no se marcan
como entregados por contener documentos de diseño. E64 espera que E60–E63
cierren sus gates de fuente; E46 espera resultados reales de E44/E45. E75 está
`in_progress`: S75.1/S75.2 ya pueden reparar el intake narrativo con E49/E55,
mientras sus handoffs profundos esperan E65.

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

- `uv run pytest -q --disable-warnings`: pass; el conteo exacto pertenece al resultado actual del runner.
- `uv run pyright`: 0 errors, 0 warnings.
- `uv run ruff check coaching escala_server validators scripts tests`: pass.
- `check_master_acceptance --mode baseline`: 36 proved / 6 unproved; todos los
  no demostrados son de E42.
- `check_governance_contract`: pass.
- `check_repository_truth`: synchronized permanece bloqueado mientras existan commits locales sin publicar; remoto, credenciales, branch y upstream pasan. El conteo exacto se obtiene del gate actual; no se normaliza mediante cambios de politica ni publicacion ciega.

## Regla de mantenimiento

Antes de crear una nueva épica, se debe: (1) consultar este registro, (2)
reutilizar o ampliar la épica que ya posea el resultado, y (3) enlazar scope,
PRD, historias, pruebas y disposición. Así se evita que un nuevo archivo
convierta trabajo no formalizado en otra “épica fantasma”.
