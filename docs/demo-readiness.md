# ScaleUp — Demo Readiness

**Objetivo de release:** una persona no técnica puede instalar ScaleUp y, usando
lenguaje natural en Claude Code o Codex, completar un recorrido guiado y obtener
un One Page Strategic Plan (OPSP) persistido.

**Última evidencia:** 2026-08-24 — auditoría de producto inicial.

## Matriz de evidencia

| Resultado esperado y fuente | Evidencia actual | Estado | Brecha e impacto | Siguiente prueba/corrección |
|---|---|---|---|---|
| Una puerta pública natural para el coach (objetivo de release; `README.md`) | La puerta pública `scaleup` y `coaching/router/__init__.py` reconocen onboarding, diagnóstico, plan en una hoja y progreso. Codex CLI descubrió `.agents/skills/scaleup`, ejecutó `coaching.router.run` con una petición natural y obtuvo la primera pregunta correcta; las pruebas también pasaron. | Parcial | El host terminó la sesión antes del mensaje final del modelo, igual que Claude. Esto acredita descubrimiento y routing real, no una conversación completa ni paridad cerrada. | Ejecutar un recorrido conversacional completo y continuo en Claude y Codex. |
| Onboarding y perfil (E8; `.scaleup/internal/skills/scaleup-welcome/SKILL.md`) | `coaching.welcome`, su validador y la instalación limpia se ejercen en `tests/test_scaleup_installer.py`. La regresión Codex limpia crea el perfil de Lumen Casa; el adapter es interno y la instalación pública expone sólo `scaleup`. | Parcial | Falta evidencia conversacional natural hasta el perfil en ambas plataformas. | Probar conversación/artefacto en Claude y Codex. |
| Diagnóstico de las cuatro decisiones (E8; `.scaleup/internal/skills/scaleup-diagnose/SKILL.md`) | Engine, validador y routing determinístico; el flujo limpio welcome→diagnose de `tests/test_scaleup_installer.py` pasó. Welcome y diagnose no son interfaces instaladas ni exponen comandos al usuario. | Parcial | Está probado por engine, no por recorrido conversacional Claude/Codex. | Añadir evidencia de recorrido natural desde estado limpio. |
| One Page Strategic Plan persistido (E10; `.scaleup/internal/skills/scaleup-strategy-opsp/SKILL.md`) | La puerta natural enruta a `coaching.opsp`; `tests/test_opsp.py` pasó. La regresión Codex instalada crea un OPSP completo y ejecuta su validador instalado contra `work/strategy/opsp.md`. | Parcial | Falta validar que un cliente recoja la conversación completa y ejecute el handoff sin intervención técnica. | Ejecutar el caso Lumen Casa del guion en ambos clientes. |
| Continuidad, tareas y sesiones (E7; `coaching/`) | La regresión Codex limpia crea el perfil de Lumen Casa y consulta progreso; el engine devuelve `next_step=diagnosis`. | Parcial | Falta demostrar recuperación tras una conversación interrumpida y reinicio real del cliente. | Crear smoke de reanudación y evidencia de artefactos. |
| Instalación limpia en Claude Code (E10; `.scaleup/install.sh`, `tests/test_scaleup_installer.py`) | El instalador admite `--target claude`; README documenta la ruta y `--status`. La prueba de instalación aislada pasó. | Parcial | Falta smoke conversacional real. | Ejecutar instalación limpia y ruta de primer uso con lenguaje natural. |
| Instalación, actualización y desinstalación en Codex (objetivo de release; E10/E12) | El instalador admite `--target codex`, instala la puerta pública y el caso de actualización/desinstalación preservando datos pasó. La regresión Codex limpia ejecuta welcome, progreso natural y OPSP validado; además Codex CLI descubrió la puerta y enruta una petición natural correctamente. | Parcial | El host cortó la sesión antes de la respuesta final del modelo. No demuestra una conversación completa en Codex ni paridad con Claude. | Ejecutar un smoke conversacional continuo desde Codex limpio. |
| Actualización y desinstalación que preserve datos de usuario (objetivo de release) | `uninstall_runtime` conserva `my-company` salvo con `--purge`; la cobertura de actualización y ambos modos de uninstall pasó. | Parcial | `--purge` elimina el runtime instalado, pero no puede localizar ni borrar `.scaleup/` u `work/strategy/opsp.md` de carpetas de proyecto arbitrarias. El producto aún no rastrea esos proyectos. | Documentar limpieza manual por carpeta de proyecto y diseñar tracking explícito antes de prometer limpieza total. |
| Guion de demo, contingencia y límites (objetivo de release; `docs/demo-script.md`) | Existe un guion con Lumen Casa, prompts naturales, artefactos, recuperación y límites. | Parcial | No sustituye un ensayo real cronometrado ni prueba ambos canales. | Ensayar el guion en Claude y Codex, registrar duración, resultado y fallos aquí. |

## Inventario de skills y orquestación

- **Entrada pública actual:** el front door `scaleup` se distribuye para los
  clientes y el router de producto reconoce solicitudes naturales. No hay otra
  interfaz pública que el usuario deba conocer.
- **Orquestación interna:** `coaching.router` aporta el routing natural y el front
  door `scaleup` es la única interfaz instalada. Los adaptadores de los flujos
  anteriores permanecen como implementación interna, no como opciones públicas.
- **Internos:** engines `coaching/`, validators y sub-skills de carga/sesión.
- **Legado/plataforma:** los adaptadores heredados viven como implementación interna
  bajo `.scaleup/internal/skills`; el instalador expone sólo la puerta pública
  `scaleup` en Claude, Hermes y Codex. `.codex-plugin/plugin.json` pertenece a
  RaiSE, no al producto.

## Ruta crítica de release

1. Construir una sola puerta pública de ScaleUp, con routing natural hacia
   bienvenida, diagnóstico, OPSP, progreso y reanudación.
2. Hacerla descubrible e instalable de modo equivalente en Claude Code y Codex.
3. Probar los recorridos de usuario y los artefactos; convertir fallos en regresiones.
4. Hacer el instalador repetible y seguro para update/uninstall, preservando datos.
5. Ensayar la demo completa con datos de ejemplo, contingencia y evidencia.

## Evidencia de checkpoint

- `python -m pytest -q` → **399 passed, 2 skipped, 1 warning preexistente**
  (2026-08-24). Incluye regresión Codex limpia: welcome → progreso con
  `next_step=diagnosis` → OPSP completo → validador instalado.
- `pytest -q tests/test_scaleup_frontdoor.py tests/test_opsp.py
  tests/test_scaleup_installer.py` → **12 passed**, sin `PYTHONPATH` manual.
  Incluye instalación Codex y confirma que welcome/diagnose son internos y que sólo
  la puerta natural se expone al usuario.
- Verificaciones de distribución: sintaxis Bash y `git diff --check` correctos; hay
  una única puerta instalada en `.claude/skills/scaleup`.
- Smoke real parcial: Codex CLI descubrió `.agents/skills/scaleup`, ejecutó el router
  para una petición natural y obtuvo la primera pregunta correcta. El host cerró la
  sesión antes del mensaje final del modelo; el mismo límite ocurrió en Claude.
- Por tanto, no se acredita todavía un recorrido conversacional completo, continuidad
  real ni paridad Claude/Codex.
