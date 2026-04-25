# Epic Brief: E7 — Agent Intelligence

## Hypothesis

Si le damos al agente memoria persistente, continuidad de sesión, gestión de tareas y alineación estratégica, entonces se comportará como un coach real que recuerda al empresario, da seguimiento a compromisos y personaliza su guía — convirtiendo sesiones aisladas en un proceso de coaching continuo.

## Success Metrics

| Metric | Target |
|--------|--------|
| Contexto cargado en session start | < 5 segundos |
| Memoria persiste entre sesiones | Perfil, scores, worksheets, historial |
| Accountability loop activo | Revisa tareas abiertas al iniciar sesión |
| Meta anual como filtro | Toda recomendación alineada al SMART goal |
| Task board funcional | TODO/DOING/DONE con vínculo a decisión |
| Company knowledge graph | Hechos de la empresa como nodos estructurados |

## Appetite

6 stories (2S + 4M). Trabajo de integración — conecta la ontología (E6) con la experiencia del usuario. Sin dependencias externas — todo file-based en `.scaleup/my-company/`.

## Rabbit Holes

- No construir base de datos — archivos YAML/markdown son la persistencia
- No session management complejo — cargar archivos al inicio, guardar al cierre
- No AI memory mágica — persistencia explícita en archivos que el empresario puede leer
- No duplicar lo que ya hace Claude Code (memory system) — complementar con datos de dominio
- El task board es markdown plano, no un sistema de project management
