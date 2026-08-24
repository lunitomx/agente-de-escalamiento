# Epic Scope: E21 — Verne Harnish Board Member

**Status:** Draft
**Dependencies:** E18 (infraestructura) + E19 (grafo de conocimiento)
**Audited:** 2026-08-24
**Tamaño:** XL

## In Scope
- **Alma de Verne** (`miembro-board/verne-harnish.md`):
  - Su framework: Rockefeller Habits, 4 Decisions, Power of One
  - Sus preguntas características: "¿Cuál es tu ROC?", "¿Tienes un Daily Huddle?", "¿Quién es tu Core Customer?"
  - Su lente: prioriza cash flow, simplicidad, ejecución, hábitos
  - Sus sesgos: prefiere acción sobre análisis, estructuras simples, accountability clara
  - Sus principios no negociables: "No surprises", "Keep things simple", "Daily Huddle every day"
- **Agente de revisión**: Verne revisa tus dailys y da observaciones
- **Consulta directa**: "Verne, ¿qué opinas de mi strategy?"
- **Integración con ciclo de sesión**: al cerrar sesión, Verne puede dar su perspectiva
- **Modo board completo**: Verne debate contigo sobre decisiones específicas

## Out of Scope
- Ingresar el libro (E19)
- Conectar skills a dashboards (E20)
- Crear otros miembros del board (Hormozi, Collins, etc. — futuras épicas)
- Procesamiento de audio/video (solo texto)

## Dependencias
- E19 (conocimiento estructurado del libro en el grafo)
- E18 (infraestructura: server, sesiones, SQLite, CLI)
- El alma debe basarse ESTRICTAMENTE en el libro — no inventar

## Gates Before Implementation

- [ ] La suite actual vuelve a verde
- [ ] Epic design aprobado
- [ ] Implementation plan aprobado
- [ ] Tamaño XL dividido en stories con criterios verificables
- [ ] Estrategia de trazabilidad al conocimiento E19 definida

## Done Criteria
- [ ] `miembro-board/verne-harnish.md` completo con framework, preguntas, lente, sesgos, principios
- [ ] Verne puede analizar un daily y dar observaciones
- [ ] Verne puede responder a "¿qué opinas de X?" con coherencia
- [ ] Integrado con escala-inicia: Verne recibe contexto de la sesión
- [ ] Los skills pueden consultar "¿qué diría Verne sobre X?"
- [ ] Tests: respuestas de Verne son coherentes con el libro
