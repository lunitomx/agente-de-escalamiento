# Autoridad de estado de épicas

## Regla canónica

El frontmatter de `work/epics/<epic>/scope.md` es la única autoridad para el
estado de una épica. El inventario ejecutable está en `governance/backlog.md`
y la disposición de cierres se rige por `governance/closure-dispositions.yaml`.

Un `brief.md`, `prd.md`, `design.md`, ADR o retrospectiva no cambia por sí solo
el estado de la épica. Sus etiquetas históricas (`draft`, `planned`,
`designed`, `accepted` o `done`) describen el documento, no la cartera. No se
deben usar para reabrir ni cerrar trabajo.

## Aplicación

- Todo documento nuevo que necesite declarar ambos conceptos usa
  `document_status` y `epic_status`; no reutiliza un `status` ambiguo.
- Los documentos activos de E44/E45 se alinearon a `in_progress` porque son
  contratos operativos actuales, no archivos históricos.
- Los documentos legados conservan su etiqueta de época. La auditoría de
  portafolio los ignora para decidir si una épica está completa, activa o
  planificada.
- Si el `scope.md` y el backlog no coinciden, se corrige el backlog/portafolio
  o se abre una reparación explícita; nunca se selecciona el estado más
  conveniente.

## Verificación de cierre

Una épica sólo puede aparecer como `complete` cuando el scope, sus criterios de
terminación, evidencia actual y toda aceptación externa requerida coinciden.
Un documento antiguo, una prueba sintética o un nombre de commit no sustituyen
esa verificación.

## Inventario de scopes

El archivo governance/scope-inventory.yaml clasifica cada scope raíz legado y cada
scope de historia que no representa una épica independiente. El comando
scripts/check_scope_inventory.py debe pasar antes de aceptar una auditoría:
detecta un scope sin clasificación, un sub-scope tratado como épica, una raíz
canónica sin epic_id o sin status, y disposiciones que no existen en la política
de cierre.

No se cambia el estado de un archivo legado por el inventario: éste registra la
disposición y la evidencia que ya lo sustentan.
