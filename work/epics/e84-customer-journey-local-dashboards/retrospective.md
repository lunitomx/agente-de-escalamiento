# E84: Customer journey proactivo y tableros locales — Retrospective

**Fechas:** 2026-09-30 · **Jira:** ESCALA-50 · **Historias:** 4 (S84.1–S84.4), todas mergeadas a main. Absorbe E73 (ESCALA-37).

## Qué entrega
- **Journey proactivo:** "muchos preguntan pero pocos compran" dispara una sola pregunta; "después" silencia 30 días.
  Entrevista de 5 preguntas cortas; "unos 100" se acepta como supuesto. El mapa separa lo que el dueño cree,
  datos con periodo y lo que dijeron clientes; "dónde se pierden más" sólo con el mismo mes; termina en una
  decisión guardada en `.escala/my-company/journey/` que entra al siguiente diagnóstico como hecho local.
- **Tableros:** "tablero de mis ventas" da máximo 2 propuestas con decisión, métricas con fuente y periodo, y
  factibilidad. Si ya existe algo (caja, tracker, progreso, research) señala eso. Con propuesta aceptada y
  números, genera HTML autocontenido (sin internet, legible en celular) + Markdown en `.escala/my-company/tableros/`.
- Ruta `dashboard` primera en el catálogo; progreso en inglés resumido en español (U7, cierra la parte de E80).

## Métricas
- Tests `coaching/journey` + `coaching/dashboard/boards`: 0 → 229 (+ tests de procedimiento). Suite completa verde salvo 3 fallas ambientales conocidas.
- Catálogo: 64 → 65 procedimientos, 65 → 66 capacidades; ningún comando nuevo para el dueño.

## Qué salió bien
- S84.2 y S84.3 corrieron en paralelo (paquetes distintos); el único choque fue la tabla de estado en scope.md.
- Reglas de honestidad como test: nunca afirmar que se entrevistó a clientes, "falta" en vez de estimar, sin números no hay tablero.
- La revisión de UX de S84.1 (30 preguntas → 5, "pocos compran" sin ruta, archivo corrupto) se corrigió antes del merge.

## Qué mejorar
- En S84.4 una tarea escribió tests sin verlos fallar primero (anotado en su retro).
- Dos tests parecen inestables en corridas combinadas: `test_e42_qualification` s42.4 y `test_master_acceptance_cli_has_truthful_modes_and_one_safe_failure`.
- Pipeline engine sigue roto para este repo (A53); ciclo manual.

## Pendiente fuera del epic (requiere al dueño o prueba real)
- M3: revisar una transcripción real para confirmar que ESCALA no insiste.
- Matriz por plataforma: sólo el núcleo verificado por tests; Codex, claude.ai/Desktop y ChatGPT Work (E85) sin verificar.
- Preguntas abiertas de S84.2–S84.4 en sus retros (dueño_dice al diagnóstico, razón "de cada 10", sin números no se genera).
