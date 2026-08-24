# Backlog: ScaleUp Agent AI

> Vista operativa del inventario canónico de work/epics/product-roadmap.md.

**Status:** Active
**Repo:** https://github.com/lunitomx/scaleupagent
**Audited:** 2026-08-24
**Next available epic ID:** E22

## Epic Inventory

| ID | Epic | Canonical Status | Notes |
|----|------|------------------|-------|
| E1 | OCR Pipeline | complete — legacy | Cerrada antes de E3; evidencia en el backlog inicial. |
| E2 | Knowledge Base | complete — legacy | Cerrada antes de E3; evolucionó hacia E6 y E19. |
| E3 | Agent Framework | complete | 5/5. |
| E4 | Validation | retired / superseded | Draft histórico sin artefactos de ejecución; cobertura parcial E13/E19/E20. |
| E5 | Distribution | retired / superseded | Draft histórico sustituido por E10/E11. |
| E6 | Knowledge Ontology | complete | 7/7; 15 worksheets reales. |
| E7 | Agent Intelligence | complete | 6/6. |
| E8 | Coaching Engine | complete | 6/6; follow-up histórico de gates individuales. |
| E9 | Value-Add Features | complete | 4/4; summary restaurado en la ruta canónica y en el bundle. |
| E10 | Cross-Platform Distribution | complete — follow-up | 9/9; instalación aislada, adapters y equivalencia determinística verificados; falta smoke conversacional. |
| E11 | Agente de Escalamiento | complete | 6/6. |
| E12 | Codex & Auto-Update | cancelled | Absorbida por E11. |
| E13 | Auditoría y Cierre | complete | 9/9. |
| E14 | Cash Dashboards | complete | 4/4. |
| E15 | Strategy Dashboards | complete | 5/5. |
| E16 | People Dashboards | complete | 6/6. |
| E17 | Execution Dashboards | complete | 7/7. |
| E18 | Escala Server | complete | 12/12. |
| E19 | Book Ingestion | complete | 5/5; esquema JSON/SQLite/API documentado. |
| E20 | Contextual Skills | complete | 4/4. |
| E21 | Verne Lens Board Member | planned — approval pending | Diseño, plan y 5 stories verificables; implementación no iniciada. |

## Active Queue

### P0 — Finish E10 Live Smoke

- [x] Suite restaurada: 389 passed, 2 skipped.
- [x] Instalación Claude/Hermes aislada en destino temporal.
- [x] Flujo welcome → diagnose → validadores desde proyectos vacíos.
- [x] Outputs equivalentes entre los bundles Claude y Hermes.
- [x] Hermes descubre los 39 skills y carga el adapter de diagnose.
- [ ] Ejecutar los slash commands mediante agentes reales. La CLI Hermes local
  no supera bootstrap por permisos de `/usr/local/lib/hermes-agent/.env`; una
  ejecución Claude/Hermes también consumiría un proveedor externo.

### P1 — E21 Approval and Implementation

Source: work/epics/e21-verne-board-member/scope.md

- [x] Suite verde
- [x] Epic design redactado
- [x] Implementation plan redactado
- [x] XL dividido en 5 stories
- [x] Trazabilidad obligatoria hacia E19 definida
- [ ] Aprobar nombre, disclosure, hooks opt-in y límite de recomendaciones
- [ ] Implementar S21.1–S21.5

## Historical Drafts E4/E5

Las stories S4.x y S5.x del backlog original nunca se ejecutaron bajo esos IDs.
Sus objetivos se distribuyeron entre E10, E11, E13, E19 y E20. Los criterios
todavía no demostrados viven como deuda en product-roadmap.md.

No reactivar ni reutilizar E4/E5. Si la deuda residual requiere una épica nueva,
usar E22.

## Conditional Ideas

Las ideas sin compromiso aprobado viven en dev/parking-lot.md.
