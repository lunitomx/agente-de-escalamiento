---
epic_id: "E45"
grounded_in:
  - ".agents/skills/scaleup-people/SKILL.md"
  - ".agents/skills/scaleup-strategy/SKILL.md"
  - ".agents/skills/scaleup-execution/SKILL.md"
  - ".agents/skills/scaleup-cash/SKILL.md"
  - ".raise/pipelines/scaleup.yaml"
  - "E43 reliable coaching loop"
  - "E44 outcome learning"
---

# Diseño E45 — Especialistas como roles, no espectáculo

## Hallazgos

| Lo que existe | Uso en E45 |
|---|---|
| Cuatro entrypoints de decisión | Son los especialistas base: People, Strategy, Execution y Cash. |
| Pipelines | Ya definen fases, gates y condiciones de paro. |
| Router de coaching | Da una primera dirección por decisión; E45 lo extiende a casos transversales. |
| E43 | Aporta la ficha, evidencia y revisión inicial. |
| E44 | Aporta decisiones anteriores y resultados relevantes. |

## Roles lógicos

| Rol | Pregunta que responde | No puede hacer |
|---|---|---|
| Coordinador | ¿Es simple o complejo? ¿Quién debe participar? | Decidir por el dueño. |
| Especialista | ¿Qué aporta mi decisión al problema? | Usar evidencia fuera de su propósito. |
| Crítico | ¿Qué supuesto, riesgo o contradicción falta? | Convertir una sospecha en hecho. |
| Verificador | ¿Los números, fechas y fuentes sostienen la conclusión? | Cambiar la evidencia. |
| Sintetizador | ¿Cuál es la mejor decisión explicable y su siguiente paso? | Ocultar desacuerdos relevantes. |

Un rol puede ejecutarse de forma secuencial en una instalación local. E45 no
requiere simultaneidad técnica; requiere independencia de responsabilidad y
evidencia revisable.

## Recorrido

```text
Ficha de decisión compleja
  → coordinador
  → especialistas pertinentes
  → crítico y verificador
  → acuerdos, desacuerdos y preguntas faltantes
  → síntesis ejecutiva única
  → decisión humana y seguimiento E44
```

## Criterios del router

El equipo se activa solo si se cumple al menos uno:

- dos o más decisiones aportan evidencia relevante;
- hay contradicción entre fuentes;
- existe riesgo material de caja, personas, estrategia o ejecución;
- la recomendación de un solo coach fue bloqueada por E43;
- el dueño solicita expresamente una revisión transversal.

Una pregunta sobre una sola métrica, tarea o documento no basta.

## Límites

- Máximo de especialistas según decisiones relevantes, más crítico y
  verificador.
- Máximo de una ronda de aclaración antes de devolver una pregunta al dueño.
- Contexto mínimo por rol; ninguna memoria completa por defecto.
- Si no hay evidencia suficiente, se detiene con una pregunta de negocio.
- La respuesta final no menciona "agentes" salvo que el empresario lo pregunte.

## Pruebas de valor

1. **Simple:** una consulta de Cash usa un solo coach y mantiene rapidez.
2. **Compleja:** caja cae por inventario, precios y ritmo comercial; Cash y
   Execution detectan tensiones distintas.
3. **Contradicción:** Strategy propone bajar precio, Cash detecta margen
   insuficiente; el desacuerdo se muestra y se pide el dato que falta.
4. **Verificación:** un periodo financiero incorrecto bloquea la síntesis.

## Decisiones de diseño

- Se reutilizan los especialistas existentes; no se crean personajes nuevos.
- La colaboración se juzga por riesgos detectados y decisión mejorada, no por
  longitud de conversación.
- La coordinación sigue local-only y no requiere un servidor u orquestador
  remoto.
- E45 no aprende ni modifica el producto; registra su resultado mediante E44 y
  entrega señales a E46 solo después de confirmación.
