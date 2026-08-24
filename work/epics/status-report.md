# ScaleUp Agent AI — Status Report

**Fecha:** 2026-08-24
**Repo:** github.com/lunitomx/scaleupagent
**Branch auditada:** main
**Baseline reconciliada:** inventario publicado hasta 4aeac46

## Resumen ejecutivo

E20 está cerrado y E21 es la única épica pendiente formal. La numeración quedó
auditada desde el backlog original: E1/E2 son épicas históricas completas y
E4/E5 fueron borradores posteriormente retirados/sustituidos. E22 es el siguiente
número disponible.

El inventario auditado y el arreglo del parser YAML ya fueron publicados. La
suite está verde con 389 pruebas aprobadas y 2 omitidas. El follow-up E10 añadió
instalación aislada, adaptación de rutas por plataforma, flujo determinístico
desde proyectos vacíos y descubrimiento oficial de los 39 skills por Hermes.

## Estado canónico

    E1–E3       ████████████████████ COMPLETE (legacy + framework)
    E4–E5       ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ RETIRED / SUPERSEDED
    E6–E11      ████████████████████ COMPLETE
    E12         ──────────────────── CANCELLED (absorbed by E11)
    E13–E20     ████████████████████ COMPLETE
    E21         ░░░░░░░░░░░░░░░░░░░░ DRAFT

| Categoría | IDs |
|-----------|-----|
| Complete | E1, E2, E3, E6, E7, E8, E9, E10, E11, E13, E14, E15, E16, E17, E18, E19, E20 |
| Cancelled | E12 |
| Retired / Superseded | E4, E5 |
| Draft | E21 |
| Siguiente número disponible | E22 |

La explicación y evidencia por épica están en work/epics/product-roadmap.md.

## Últimos entregables

### E18 — Escala Server

- Servidor HTTP local y API routing.
- 22 dashboards interactivos.
- Persistencia SQLite y migración desde YAML.
- Memoria, grafo y ciclo escala-inicia / escala-cierra.

### E19 — Book Ingestion & Knowledge Graph

- 406 capítulos parseados.
- 42 entidades y 59 relaciones.
- 3 endpoints de conocimiento.
- 78 pruebas registradas al cierre de la épica.

### E20 — Contextual Skills

- Endpoint de contexto con validación.
- Panel contextual en 22 dashboards.
- Helper get_scaling_context() para coaching.
- Pruebas de integración del pipeline.

## Estado técnico actual

Ejecución auditada:

    uv run --python 3.12 --with pytest --with pyyaml pytest -q
    389 passed, 2 skipped, 1 warning

Aceptación E10:

1. Instalación Claude/Hermes bajo destino temporal.
2. Welcome → diagnose → validadores desde dos proyectos vacíos.
3. Outputs y routing equivalentes entre plataformas.
4. Los 39 skills fueron descubiertos por el cargador oficial de Hermes.

La ejecución conversacional mediante proveedor real no se realizó. La CLI
Hermes v0.20.5 está bloqueada durante bootstrap por permisos de su `.env` de
instalación; Claude Code está disponible, pero invocarlo consumiría un modelo
externo.

## Pendiente inmediato

1. Ejecutar el smoke conversacional E10 cuando se autorice consumo de modelo y
   se repare el bootstrap de Hermes.
2. Abrir E21 con diseño, plan e historias antes de implementar.

## Drift corregido por esta auditoría

- E1/E2 ya no aparecen como números inexistentes: fueron épicas históricas.
- E4/E5 ya no aparecen como próximas épicas activas.
- El roadmap incluye E18–E21.
- El total real de worksheets se reconoce como 15, no 34.
- Las rutas canónicas del coaching engine se reconocen bajo coaching/.
- coaching/summary/ fue restaurado en la ruta canónica y vuelve a distribuirse
  para que scaleup-close conserve su contrato.
- El esquema E19 quedó formalizado para JSON, SQLite, memoria y API.
- La dependencia de E21 se expresa como E18 + E19; E20 no es prerequisito.

---

*Actualizado y auditado: 2026-08-24*
