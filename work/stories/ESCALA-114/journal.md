## Phase: start (S87.7 · ESCALA-114) — 2026-10-20

- Worktree `story/s87.7/caja-de-arena` desde main 0b72e7ee; sync-dev-branch: skipped (in-worktree).
- Jira ESCALA-114: Tareas por hacer → En curso.
- `raise_story_open` no se usó: la rama ya existía (crearía `branch-exists`). Story y scope escritos a mano
  como en S87.4-S87.6: `work/epics/e87-strategy-workbook-completo/stories/s87.7-{story,scope}.md`.
- Seguimientos del orquestador agregados al scope (4): encabezado paso 1 en inglés, `find_worksheet` sin
  `name_es`, "?.:" en Revisión Final, prompt de IA oculto. Causas ubicadas en `coaching/worksheet/__init__.py`.
- Hallazgos: C6 dice `actividades` pero el id real es `actividades-elegidas`. Tips triangulados:
  sandbox f2/f3/f4, strategy-canvas f2/f3/f4. Tarjeta `tools/sandbox.yaml` ya corregida (S87.1).
  `total_worksheets` hoy 18 → 20.

## Phase: design (S87.7 · ESCALA-114) — 2026-10-20

- Diseño: `work/epics/e87-strategy-workbook-completo/stories/s87.7-design.md` (moderate, 5 pts).
- D1: el lienzo es vista derivada + 1 paso propio `decision` ("¿a qué le dices que no?"). Motivo: `Guide.steps` exige ≥1
  y el flujo start→step→Revisión→save ya está probado; solo-lectura pediría una rama nueva del motor.
- D2-D5: `DerivedSource.title`; autoderivación en `ToolGuide` (campo `id`), registro/campos en `__init__.derived_errors`;
  solo hojas `status: completed`; "Falta" por campo; `required: false` sin guardar → se omite; `derived_blocks` puro en view.py.
- Id real usado: `actividades-elegidas`.
- D7/D8: registro gana `name_es` corto + `time_es` (20 entradas); mapas de dificultad/decisión; un solo buscador
  (`engine.find_worksheet`, sin acentos) al que delega `__init__`. D9 `label_heading` (Revisión + .md). D10 prompt de IA visible.
- Tips: los 6 usados ya tenían ≥3 familias. Complemento fuera de Scaling Up para sandbox f3 (Danish Lead Co.),
  strategy-canvas f2 (HBR Coherence Premium) y f3 (Umbrex); `added_by: S87.7`. test_e87_research_tips: 44 de 44.
- Hotspots listados: registro 18→20, test_root, test_guide:187, test_view, cobertura pending 7/12/28/29, E6 85/81 regenerar.
- Grafo sin patrones útiles; sin drift-hotspots.json; portafolio additive.
