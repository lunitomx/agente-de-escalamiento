# E18: Escala Server, Interactive Dashboards & Memory System

## Hypothesis

Los dashboards visuales de Escala (E14-E17) son estáticos — muestran datos de ejemplo pero no se conectan con los datos reales que el usuario ingresa en los worksheets. Tampoco hay memoria entre sesiones de coaching. Si construimos un sistema que integre:

1. Un servidor local que sirva los dashboards con datos en vivo desde SQLite
2. Memoria neurosimbólica y grafo de conocimiento (como RaiSE)
3. Un ciclo de sesión con inicio (escala-inicia) y cierre (escala-cierra) que capture contexto, detecte cambios y persista aprendizaje

...el usuario podrá visualizar y manipular su negocio en tiempo real, y cada sesión será más inteligente que la anterior.

## Success Metrics

- Power of One con sliders funcionales que persisten a SQLite
- Navegación Home → 4 Decisiones → Herramientas → Dashboard
- `escala-inicia` carga contexto, memoria, grafo y detecta cambios desde último cierre
- `escala-cierra` captura aprendizaje, diff de datos, actualiza grafo
- `escala-server start` arranca el servidor con los 22 dashboards
- SQLite con 7 tablas: companies, worksheets, sessions, changes_log, memory_facts, entities, relationships
- 12 historias completas

## Appetite

Épica completa — 12 historias. Prioridades:
1. S18.3 Power of One (piloto interactivo)
2. S18.8 SQLite + S18.10/18.11 ciclo de sesión
3. S18.9 Memoria y grafo
4. S18.4-S18.7 Suites restantes

## Rabbit Holes

- No sobreingeniería — server con http.server nativo, sin Flask/FastAPI
- No tocar HTMLs existentes más de lo necesario — inyectar fetch() + sliders
- La memoria neurosimbólica debe ser simple al inicio (facts con trust score, sin NLP complejo)
- Los HTMLs deben seguir funcionando sin server (modo degradado)
- escala-inicia/cierra deben funcionar sin server (solo SQLite)
- Estrategia/People/Execution son más visualización que edición — priorizar Cash

## No-Go (actualizado)

- NO autenticación multi-usuario — es local
- NO despliegue cloud
- NO dependencias externas (todo Python stdlib: http.server + sqlite3)
- NO interfaz mobile nativa (responsive sí)
