---
epic_id: "E44"
grounded_in:
  - "escala_server/session/session_close.py"
  - "escala_server/memory_engine.py"
  - "escala_server/graph_engine.py"
  - "escala_server/executive/cockpit.py"
  - "existing tasks, sessions and worksheets"
---

# Diseño E44 — Aprender de resultados, no de conversación suelta

## Hallazgos

| Lo que existe | Uso en E44 |
|---|---|
| Cierre de sesión | Ya captura decisiones, aprendizajes y cambios; E44 les añade seguimiento verificable. |
| Memoria con confianza | Ya permite disminuir o aumentar peso; E44 define cuándo es legítimo hacerlo. |
| Grafo local | Ya conecta hechos y entidades; E44 relaciona decisión, acción y resultado. |
| Tareas y sesiones | Proveen responsables, cadencia y lugar natural para preguntar. |
| Cockpit ejecutivo | Muestra la vista de decisiones y resultados sin exponer el almacenamiento interno. |

## Registro empresarial propuesto

Cada ciclo conserva cinco piezas claras:

| Pieza | Pregunta que responde |
|---|---|
| Recomendación | ¿Qué sugirió ESCALA y con qué evidencia? |
| Decisión | ¿El dueño aceptó, rechazó o aplazó? |
| Acción | ¿Quién hará qué y para cuándo? |
| Resultado | ¿Qué ocurrió o qué sigue sin medirse? |
| Aprendizaje | ¿Qué puede reutilizarse, con qué confianza y por cuánto tiempo? |

## Recorrido

```text
Recomendación confiable
  → decisión humana
  → acción y expectativa
  → revisión en la cadencia correcta
  → resultado observado
  → confirmación o corrección humana
  → aprendizaje local reutilizable
```

No existe una flecha directa de "recomendación" a "aprendizaje". El resultado y
la revisión humana son obligatorios.

## Reglas de interpretación

- Un resultado confirma que algo cambió; no prueba automáticamente la causa.
- La causalidad solo se registra cuando la evidencia la sostiene o el dueño la
  confirma de forma informada.
- La falta de resultado es un estado válido, no un fracaso del empresario.
- La confianza baja por evidencia desmentida o vieja; no por una opinión del
  agente.
- Un aprendizaje relacionado con People requiere consentimiento y lenguaje no
  diagnóstico.

## Experiencia

El empresario verá solamente:

- "Decidimos esto".
- "La acción corresponde a esta persona y se revisa en esta fecha".
- "Esto cambió / esto aún no sabemos".
- "¿Confirmas que esta es una lección para la próxima vez?".

## Pruebas de valor

1. Una recomendación de Cash genera una acción de cobranza y se revisa en la
   weekly.
2. Una prioridad de Execution queda sin resultado y el sistema no la marca como
   fallida ni inventa explicación.
3. Una lección corregida por el dueño deja de influir como hecho confiable.
4. Un dato sobre una persona no se promueve sin el control de consentimiento.

## Decisiones de diseño

- Se extiende la memoria local existente; no se crea un lago de datos nuevo.
- Los estados de decisión y revisión son explícitos y reversibles.
- El cockpit consume una vista ejecutiva, no una cadena de razonamiento.
- E44 no usa colaboración multi-agente: debe probar el valor del seguimiento
  antes de aumentar complejidad en E45.
