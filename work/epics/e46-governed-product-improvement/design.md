---
epic_id: "E46"
grounded_in:
  - "escala-skills/escala-bugreport/SKILL.md"
  - "escala-agent/skills/escala-evolve/SKILL.md"
  - "work/epics/e24-escala-evolve/scope.md"
  - "work/epics/e1801-class-to-skill-learning-loop/"
  - "validators/skill_golden_cases.py"
  - "E44 outcome learning and E45 specialist collaboration"
---

# Diseño E46 — Mejorar con evidencia y permiso

## Hallazgos

| Lo que existe | Decisión de E46 |
|---|---|
| Bugreport local | Se reutiliza como señal anónima; no se convierte en telemetría automática. |
| E1801 | Aporta sugerencias de clases revisables, no cambios directos de skills. |
| Golden cases y changelog | Se reutilizan para proteger comportamiento antes y después de un cambio. |
| E24/escala-evolve | Aporta la intención de detectar patrones, pero su auto-patch no se reactiva. |
| E44 | Aporta resultados confirmados o rechazados, no conversaciones sueltas. |
| E45 | Puede generar señal de que la colaboración agregó o no agregó valor. |

## Ciclo de mejora

```text
Señal local y redactada
  → patrón reproducible o incidente severo
  → propuesta con evidencia y riesgo
  → casos antes/después + regresión
  → aprobación humana explícita
  → cambio versionado y rollback probado
  → medición posterior
```

La transición de una etapa a otra siempre queda registrada. No hay una flecha
automática que aplique una propuesta.

## Registros propuestos

| Registro | Contenido mínimo | Quién puede cambiarlo |
|---|---|---|
| Señal | Tipo, consentimiento, identidad omitida, severidad, resumen redactado. | Quien reporta o el intake local. |
| Patrón | Señales relacionadas, repetición, evidencia permitida, confianza. | Revisor de producto. |
| Propuesta | Problema, cambio sugerido, impacto, riesgos, casos y estado. | Equipo de producto. |
| Aprobación | Persona responsable, decisión, fecha, razón y versión. | Humano autorizado. |
| Medición | Resultado posterior, regresiones, decisión de conservar o revertir. | Humano con evidencia. |

## Reglas de seguridad

- La señal falla cerrada si conserva identidad, datos empresariales o fragmentos
  privados sin consentimiento.
- Los archivos fuente permanecen locales y no se copian al registro de mejora.
- La propuesta puede sugerir un cambio, pero nunca escribirlo por sí sola.
- Toda promoción requiere pruebas, aprobación humana y un rollback ejecutable.
- La medición posterior puede concluir "no sabemos"; no fuerza una narrativa de
  éxito.

## Pruebas de valor

1. Un bug report anónimo repetido genera un patrón sin copiar el contenido de la
   empresa.
2. Una propuesta de Cash pasa sus casos propios pero rompe un caso de Execution;
   queda bloqueada.
3. Una propuesta aprobada conserva versión y se revierte en un ensayo controlado.
4. La medición posterior muestra que el problema no disminuyó y activa revisión o
   rollback, sin culpar al usuario.

## Decisiones de diseño

- E46 sustituye el alcance pendiente de E24; no intenta reparar su historial ni
  declarar sus stories como terminadas.
- La mejora se modela como un flujo de producto y evidencia, no como una
  conversación libre de auto-crítica.
- El sistema local puede preparar paquetes para compartir manualmente, pero no
  envía issues, diagnósticos ni información de usuarios por sí solo.
- El estándar de promoción es comportamiento protegido y aprobación humana, no
  solo una respuesta de modelo que parezca mejor.
