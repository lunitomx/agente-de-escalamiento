# Retrospectiva: E22 — Memoria Empresarial Integrada

**Fecha:** 2026-08-26  
**Resultado:** PASS — cierre local

## Resultado alcanzado

E22 deja a ScaleUp con una memoria empresarial local-first y única por
proyecto: instala el runtime necesario, migra el estado YAML de forma
idempotente a SQLite, recupera sólo contexto confirmado al iniciar, y propone
hechos, decisiones o patrones para confirmación explícita antes de guardarlos.
La puerta pública conserva lenguaje natural y degrada al flujo existente si la
memoria no está disponible, vacía o corrupta.

Las siete historias del scope están completas; S22.2--S22.7 se integraron a
`main` mediante merges verificables y S22.1 quedó materializada en el contrato
y ADR iniciales de la épica. No quedan casillas de aceptación ni historias
abiertas en `scope.md`.

## Métricas y evidencia

- Suite final acreditada: **529 passed, 2 skipped**.
- La gate completa se ejecutó con
  `RAISE_TEST_WORKER_BUDGET=0 rai gate check gate-tests`: **PASS**. Emite el
  aviso no bloqueante `RAISE-5391` por no tener `--scope` en contexto workflow;
  no altera el veredicto.
- Gates focalizadas de runtime, migración, contexto, cierre, continuidad,
  conversación e instalador: **PASS**; `gate-lint` y `gate-format`: **PASS**.
  `gate-types`: **SKIPPED** correctamente porque el manifiesto no define
  `type_check_command`.
- La evidencia offline
  `work/evidence/e22-client-smoke/2026-08-26/verify.sh` verificó hashes,
  atestación y secuencia semántica de Claude y Codex: **PASS**.
- La matriz instalada acredita pausa natural, declaración permitida,
  confirmación `sí`, segunda sesión y recuperación; también aislamiento,
  backup/restore, fallback y uninstall conservador.

## Escapes detectados y corregidos

1. La revisión de S22.6 detectó que texto sensible o técnico podía llegar a
   una propuesta de memoria. Se centralizó una política canónica ES/EN y se
   aplicó en captura, proyección y render; se añadieron regresiones adversarias.
2. La revisión de S22.7 detectó que el instalador copiaba ampliamente
   `.scaleup/agent`, con riesgo de distribuir conversaciones, perfiles, DB o
   backups de una empresa. Se sustituyó por una allowlist de runtime y una
   prueba negativa que siembra esos datos antes de instalar los tres destinos.
3. La evidencia de cliente se hizo verificable offline con hashes, atestación
   y transcripciones redactadas, en lugar de depender de procesos temporales
   no conservados.

## Patrones que se refuerzan

- La memoria empresarial debe cruzar tres fronteras: persistencia local,
  recuperación pública y distribución. La política de texto por sí sola no
  protege el bundle.
- La confirmación explícita y la proveniencia por versión evitan que una
  inferencia del modelo se convierta en dato de negocio.
- Una matriz de release útil ejecuta el artefacto instalado, no imports desde
  el checkout, y verifica tanto payload permitido como payload prohibido.
- Los warnings ajenos al scope se registran separados y no se usan para
  debilitar gates ni expandir una historia cerrada.

## Límites y seguimiento

- Hermes tiene cobertura determinista del bundle/runtime y front door, pero no
  se declara paridad del cliente Hermes real. En este host `hermes --help` no
  puede leer `/usr/local/lib/hermes-agent/.env` y termina en `PermissionError`.
  La siguiente evidencia necesaria es ejecutar ese cliente con configuración
  legible en una raíz temporal con `.hermes/skills/scaleup` y observar discovery
  y conversación.
- No hubo `Run ID` de pipeline al invocar el cierre; se continuó por la
  autorización explícita del objetivo E22 y se registró un cierre estrictamente
  local, sin inventar transición remota.
- No existe `.raise/backlog.yaml` ni hay backlog remoto en alcance. Por ello no
  se actualizó `fixVersion` ni estado remoto; esas transiciones son
  engine-owned y no se sustituyeron con datos sintéticos.
- No se realizó push. El tag y el commit son locales y quedan listos para la
  publicación que autorice el responsable.
