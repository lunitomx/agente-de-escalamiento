---
epic_id: "E40"
title: "Executive Cockpit and Coaching"
status: "in_progress"
created: "2026-07-22"
mission: "escala-local-v2-plan-maestro-2607202112"
---

# Epic Brief: Executive Cockpit and Coaching

## Hypothesis

Para el empresario que necesita entender dónde está su empresa y qué debe hacer después, un cockpit ejecutivo local que pregunta antes de concluir, puntúa las cuatro decisiones con evidencia y conserva el trabajo de ejecución convertirá los skills separados en una guía continua y verificable. A diferencia de un dashboard decorativo o un agente hospedado, la propuesta conservará hechos, inferencias y desconocidos, enlazará cada recomendación con evidencia local y no moverá la autoridad fuera de la máquina instaladora.

## Success Metrics

- **Leading:** una empresa sintética completa onboarding, obtiene cuatro scores 0–100, puede abrir el dolor principal hasta sus fuentes/preguntas/acción, y recibe una ruta explícita a People, Strategy, Execution o Cash.
- **Lagging:** goals, priorities, tasks, owners, due dates, progress and session continuity sobreviven un reinicio local y el cockpit reproducido no inventa datos ni contiene rutas de máquina, endpoints cloud o estado en el exchange.

## Appetite

L — cuatro stories (S40.1–S40.4), con un walking skeleton de onboarding → diagnóstico → cockpit → coaching → persistencia.

## Scope Boundaries

### In (MUST)

- Onboarding guiado con perfil validado y campos `fact`, `inference` o `unknown`.
- Diagnóstico 0–100 separado para People, Strategy, Execution y Cash, con evidencia, frescura, bloqueadores y preguntas.
- Cockpit visual local con drill-down del dolor principal a evidencia, preguntas y siguiente acción.
- Visión y OPSP-style strategy discovery, routing de coaching y persistencia local de ejecución/continuidad.
- Reglas fail-closed: nunca inventar datos, nunca convertir ausencia en fallo personal, nunca escribir autoridad en Drive/OneDrive.

### In (SHOULD)

- HTML/JSON deterministas para inspección local y exportación manual a una carpeta ordinaria.
- Compatibilidad de entrada con source IDs y reportes ya producidos por E37–E39.

### No-Gos

- DISC, correlación psicológica o evaluación de desempeño individual → parking lot / decisión posterior de People.
- Servicio hospedado, base de datos cloud, OAuth, Slack/Teams/Calendar o workers remotos → prohibidos por E36/E37.
- Instalador nativo, actualización/rollback y aceptación de empresarios reales → E41/E42.
- Puntuaciones sustentadas solo en ausencia de archivos o sentimientos inferidos.

### Rabbit Holes

- Construir otra base de datos: el estado canónico sigue siendo la SQLite local/`data_root` validada.
- Crear un frontend hospedado para demostrar el cockpit: un artefacto HTML local es suficiente para esta épica.
- Pretender un OPSP completo cuando faltan respuestas: las decisiones pendientes deben quedar visibles como `unknown`/unresolved.
