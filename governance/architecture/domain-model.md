---
type: architecture_domain_model
project: "ScaleUp Agent AI"
status: draft
bounded_contexts:
  - name: onboarding
    modules: [scaleup-welcome]
  - name: diagnosis
    modules: [scaleup-diagnose, scaleup-progress]
  - name: people
    modules: [scaleup-people, scaleup-people-values, scaleup-people-fac, scaleup-people-topgrading]
  - name: strategy
    modules: [scaleup-strategy, scaleup-strategy-opsp, scaleup-strategy-7strata, scaleup-strategy-swot]
  - name: execution
    modules: [scaleup-execution, scaleup-execution-rhythms, scaleup-execution-priorities, scaleup-execution-rockefeller]
  - name: cash
    modules: [scaleup-cash, scaleup-cash-ccc, scaleup-cash-power1, scaleup-cash-acceleration]
shared_kernel:
  knowledge-base: "Contenido estructurado del libro Scaling Up"
  templates: "Worksheets y herramientas reutilizables"
---

# Domain Model: ScaleUp Agent AI

> Bounded contexts del agente ScaleUp

## Bounded Contexts

### Onboarding
Primer contacto con el empresario. Recoge perfil de la empresa (industria, tamaño, etapa, retos) y prepara el contexto para diagnóstico.
- **Skills:** `scaleup-welcome`
- **Artifacts:** Company profile en memoria del agente

### Diagnosis
Evaluación del estado actual de la empresa en las 4 decisiones de Scaling Up. Identifica fortalezas, debilidades y prioridades de acción.
- **Skills:** `scaleup-diagnose`, `scaleup-progress`
- **Artifacts:** `templates/diagnosis-report.md`
- **Inputs:** Company profile del onboarding

### People
Personas correctas en los asientos correctos. Core values, accountability, topgrading.
- **Skills:** `scaleup-people`, `scaleup-people-values`, `scaleup-people-fac`, `scaleup-people-topgrading`
- **Artifacts:** `templates/function-accountability-chart.md`

### Strategy
Dirección estratégica clara. BHAG, brand promise, OPSP, 7 Strata, SWOT.
- **Skills:** `scaleup-strategy`, `scaleup-strategy-opsp`, `scaleup-strategy-7strata`, `scaleup-strategy-swot`
- **Artifacts:** `templates/opsp.md`

### Execution
Disciplina de ejecución. Meeting rhythms, prioridades trimestrales, Rockefeller Habits.
- **Skills:** `scaleup-execution`, `scaleup-execution-rhythms`, `scaleup-execution-priorities`, `scaleup-execution-rockefeller`
- **Artifacts:** `templates/meeting-rhythm-planner.md`, `templates/rockefeller-habits-checklist.md`

### Cash
Flujo de efectivo y aceleración. Cash Conversion Cycle, Power of One, estrategias de aceleración.
- **Skills:** `scaleup-cash`, `scaleup-cash-ccc`, `scaleup-cash-power1`, `scaleup-cash-acceleration`
- **Artifacts:** `templates/cash-conversion-cycle.md`, `templates/power-of-one.md`

## Shared Kernel

| Module | Used By | Description |
|--------|---------|-------------|
| Knowledge Base | All contexts | Contenido del libro Scaling Up estructurado por las 4 decisiones |
| Templates | Diagnosis, People, Strategy, Execution, Cash | Worksheets rellenables que el agente guía al empresario a completar |
| Company Profile | All contexts | Datos de la empresa recolectados en onboarding, accesibles a todos los skills |
