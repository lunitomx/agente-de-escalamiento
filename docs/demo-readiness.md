# ScaleUp — Demo Readiness

**Objetivo de release:** una persona no técnica puede instalar ScaleUp y, usando
lenguaje natural en Claude Code o Codex, completar un recorrido guiado y obtener
un One Page Strategic Plan (OPSP) persistido.

**Última evidencia:** 2026-08-26 — matriz automatizada de bundle limpio para Claude, Codex y runtime Hermes; continuidad, privacidad, fallback y retención local verificados.

## Matriz de evidencia

| Resultado esperado y fuente | Evidencia actual | Estado | Brecha e impacto | Siguiente prueba/corrección |
|---|---|---|---|---|
| Una puerta pública natural para el coach (objetivo de release; `README.md`) | `scaleup` usa una conversación estatal sin JSON; agentes independientes completaron el recorrido y una reanudación en Claude Code y Codex. | Funciona | Sin brecha crítica conocida. | Mantener la regresión de conversación y el smoke de ambos clientes por release. |
| Onboarding y perfil (E8; `.scaleup/internal/skills/scaleup-welcome/SKILL.md`) | La frase combinada de Lumen Casa crea el perfil y lleva a la primera pregunta 1–5 en ambos clientes desde instalación limpia. | Funciona | Las respuestas de perfil incompletas se vuelven a pedir una a una. | Cubierto por `test_scaleup_conversation.py`. |
| Diagnóstico de las cuatro decisiones (E8; `.scaleup/internal/skills/scaleup-diagnose/SKILL.md`) | Los dos clientes guardaron 20 respuestas una a una, priorizaron Efectivo y retomaron el estado entre sesiones. | Funciona | Requiere la escala explicada 1–5 para cada pregunta. | Mantener el smoke de 20 turnos y regresión de reanudación. |
| One Page Strategic Plan persistido (E10; `.scaleup/internal/skills/scaleup-strategy-opsp/SKILL.md`) | Claude y Codex crearon `work/strategy/opsp.md` válido y `completed` con datos ficticios, desde frases naturales. | Funciona | Prioridades requieren tres partes claras: prioridad, responsable e indicador. | Mantener validación de artefacto y la frase de valores con “y”. |
| Continuidad, tareas y sesiones (E7; `coaching/`) | Sesiones nuevas en ambos clientes respondieron `¿Cómo vamos y qué sigue?`, recuperaron scores, plan y siguiente paso. La matriz E22 además acredita pausar → decisión → `sí` → retomar desde el front door instalado. | Funciona | Sólo una declaración confirmada entra a memoria local; datos sensibles o técnicos se rechazan. | Mantener smoke de sesión nueva y matriz E22 por release. |
| Instalación limpia en Claude Code (E10; `.scaleup/install.sh`, `tests/test_scaleup_installer.py`) | Instalación real temporal, discovery, recorrido completo y continuidad pasaron con la allowlist del frontdoor. | Funciona | Sin brecha crítica conocida. | Verificar al publicar una nueva versión. |
| Instalación, actualización y desinstalación en Codex (objetivo de release; E10/E12) | La ruta global documentada `~/.codex/skills` fue descubierta; recorrido completo, continuidad y update/uninstall pasaron. | Funciona | Un destino temporal no cambia `CODEX_HOME`; no usarlo como smoke de discovery. | Mantener smoke global aislado y limpieza posterior. |
| Actualización y desinstalación que preserve datos de usuario (objetivo de release) | Update/uninstall conserva `my-company`; `--purge` elimina sólo el runtime seleccionado. | Funciona con limitación | Los artefactos de proyectos se limpian manualmente, ya documentado. | Diseñar tracking de proyectos sólo después del release. |
| Guion de demo, contingencia y límites (objetivo de release; `docs/demo-script.md`) | Guion Lumen Casa alineado al flujo una pregunta a la vez; ensayos reales pasaron en ambos clientes. | Funciona | El tiempo activo técnico fue menor que una presentación humana; el guion reserva espacio para explicación y decisiones. | Ensayo humano facilitado antes de la presentación. |

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

## Evidencia de checkpoint histórico (superado)

- `python -m pytest -q` → **404 passed, 2 skipped, 1 warning preexistente**
  (2026-08-24). Incluye regresión Codex limpia: welcome → progreso con
  `next_step=diagnosis` → OPSP completo → validador instalado.
- `pytest -q tests/test_scaleup_conversation.py tests/test_scaleup_frontdoor.py tests/test_opsp.py
  tests/test_scaleup_installer.py` → **17 passed**, sin `PYTHONPATH` manual.
  Incluye instalación Codex y confirma que welcome/diagnose son internos y que sólo
  la puerta natural se expone al usuario.
- Ensayo cronometrado automatizado en instalación Codex limpia, con Lumen Casa:
  onboarding → diagnóstico (prioridad efectivo) → OPSP completo → continuidad →
  validador instalado, **PASS en 1 segundo**. Es evidencia de motor y artefactos,
  no sustituye un ensayo conversacional en cliente.
- Verificaciones de distribución: sintaxis Bash y `git diff --check` correctos; hay
  una única puerta instalada en `.claude/skills/scaleup`.
- Smoke real parcial: Codex CLI descubrió `.agents/skills/scaleup`, ejecutó el router
  para una petición natural y obtuvo la primera pregunta correcta. Claude Code también
  descubrió y lanzó el skill `scaleup`; su política local negó el comando Python del
  router antes de que el modelo pudiera responder. El host no permite autorizar ese
  comando de forma suficientemente acotada en este smoke.
- Limitación superada por el ensayo completo de aceptación documentado al final.
## Actualización de desbloqueo — 2026-08-24

- Se reemplazó el router embebido `python3 -c` por el ejecutable fijo y auditable `.scaleup/bin/scaleup-frontdoor`; el instalador lo distribuye en cada runtime y la skill instalada apunta a esa ruta absoluta.
- **Claude Code, smoke real:** descubrió la única skill `scaleup`, ejecutó exclusivamente ese comando con una allowlist específica, no registró denegaciones y devolvió la primera pregunta de onboarding.
- **Codex, smoke real:** descubrió `.agents/skills/scaleup`, ejecutó el mismo comando y devolvió la misma primera pregunta.
- El ejecutable cubre bienvenida, diagnóstico, plan, progreso y validación; el límite de primer turno de este checkpoint fue superado por los ensayos completos posteriores.
- Reproducción registrada: Claude Code se ejecutó con `--allowedTools "Bash(.scaleup/bin/scaleup-frontdoor *)"` y Codex con `codex exec --ephemeral --json --approve-for-me`; ambos descubrieron `scaleup`, llamaron al ejecutable y devolvieron la primera pregunta. No se registran esos comandos como sustituto de la demo completa.

## Checkpoint conversacional — 2026-08-24

- Un ensayo independiente reveló que el cliente tenía que adivinar JSON y claves internas tras la primera pregunta. Se corrigió con `scaleup-frontdoor conversation`: una máquina de estados local que recibe solamente la frase humana, persiste el perfil, las 20 respuestas del diagnóstico y el plan parcial, y devuelve una sola pregunta siguiente.
- La regresión incluye la frase real de demo `Se llama Lumen Casa. Vendemos iluminación decorativa… Somos 28 personas.`, respuesta `todavía no lo sé`, abandono/reanudación, plan persistido válido e instalación Codex limpia.
- Claude Code, desde instalación limpia, acreditó discovery de `scaleup`, primer turno, perfil tras esa frase exacta, siguiente pregunta 1–5 y reanudación con petición natural de plan.
- Codex usa globalmente `$CODEX_HOME/skills` (por defecto `~/.codex/skills`); la instalación normal apunta ahí. Un `--destination-root` temporal no cambia la ruta que consume el cliente, por lo que no es evidencia de discovery. El recorrido completo posterior confirmó la carga global y la conversación natural.
- Estado de release en este checkpoint: motores, instalación y flujo natural determinista verdes; el ensayo completo posterior cerró la evidencia de ambos clientes.
- El primer ensayo completo de Codex alcanzó 23 turnos exitosos (inicio, intake, diagnóstico completo y entrada a plan) antes de encontrar que una lista natural de valores con “y” no se interpretaba. Se añadió la regresión de esa frase exacta, se corrigió el parser y el tramo fue repetido con éxito en el cliente.

## Ensayo de aceptación en clientes — 2026-08-24

- **Codex, agente independiente:** desde instalación global limpia, completó inicio, perfil con la frase combinada de Lumen Casa, 20 respuestas una a una, diagnóstico (Efectivo 1 como foco), plan persistido válido y una sesión nueva de progreso. El dashboard final muestra Estrategia 1/4 y “Plan de la empresa en una hoja”, sin siglas, comandos ni etiquetas internas.
- **Claude Code, agente independiente:** completó el mismo recorrido con la allowlist limitada al frontdoor; todos los turnos terminaron sin denegaciones. Una sesión nueva recuperó el plan, los scores y el siguiente paso en lenguaje llano; también muestra Estrategia 1/4.
- Ejecución observada: Claude 5–6 min activos y Codex 14–15 min de ejecución efectiva; son mínimos técnicos sin pausas de conversación. El guion guiado reserva 60–90 min para explicar, decidir y resolver preguntas con la persona.
- Correcciones nacidas del ensayo: conversación estatal sin JSON, intake de frase combinada, valores con enumeración natural y dashboard que reconoce el plan completado. Cada una tiene regresión.
- Resultado: criterios críticos de instalación, discovery global, recorrido natural, artefacto OPSP válido y continuidad fueron verificados en ambos clientes con datos ficticios.


## Checkpoint de release E22 — 2026-08-26

- `rai gate check gate-tests --scope tests/test_scaleup_installer.py` instala Claude, Codex y Hermes en raíces temporales limpias y conversa sólo mediante el `scaleup-frontdoor` copiado: pausar → declaración → `sí` → nueva sesión → retomar. Verifica proveniencia, aislamiento y ausencia de datos empresariales en el runtime.
- El smoke acredita rechazo de texto sensible, fallback con DB ausente/vacía/corrupta sin alterar memoria, backup/restore offline, rechazo de backup inválido, actualización y uninstall conservadores. `--purge` elimina sólo el runtime del target solicitado.
- **Hermes:** el bundle y su front door pasaron el smoke determinista. No se declara paridad del cliente Hermes: en este host `/usr/local/bin/hermes --help` no inicializa porque no puede leer `/usr/local/lib/hermes-agent/.env` (`PermissionError`). Para cerrar la brecha hace falta un cliente Hermes con permisos de lectura de su configuración, en raíz temporal, que descubra `.hermes/skills/scaleup` y ejecute una conversación real contra el front door.
