---
epic_id: "E43"
grounded_in:
  - ".raise/pipelines/scaleup.yaml"
  - "escala_server/financial/"
  - "escala_server/meetings/"
  - "escala_server/executive/"
  - "escala_server/workspace/authority.py"
  - "E34 evidence system and E35 golden cases"
---

# Diseño E43 — Un ciclo de confianza, no otro agente

## Hallazgos

| Lo que existe | Cómo se reutiliza |
|---|---|
| Pipelines de ScaleUp | Dan la secuencia y condiciones para People, Strategy, Execution y Cash. |
| Ingesta local de archivos | Aporta documentos sin cambiar la autoridad local. |
| Análisis de Cash y reuniones | Son los dos primeros recorridos de valor real. |
| Cockpit y coaching | Reciben una respuesta estructurada y la convierten en siguiente acción. |
| Evidencia de voz del cliente | Es el precedente de citar fuente o declarar que falta evidencia. |
| Golden cases | Prueban comportamiento sin depender de una respuesta textual exacta. |

## Componentes propuestos

| Componente | Responsabilidad | Lo que ve el empresario |
|---|---|---|
| Ficha de decisión | Captura objetivo, área, horizonte y resultado esperado. | Una confirmación breve de la pregunta. |
| Paquete de evidencia | Agrupa fuentes, periodo, datos faltantes y certeza. | Fuentes utilizadas y huecos relevantes. |
| Selector de análisis | Elige Cash, reuniones, estrategia o ejecución según la evidencia. | Nada adicional salvo que falte una fuente. |
| Revisión crítica | Separa hecho, inferencia y desconocido; detecta contradicciones. | Dudas y límites expresados claramente. |
| Respuesta ejecutiva | Sintetiza decisión, evidencia, riesgo, acción y siguiente pregunta. | Un solo coach, una sola respuesta. |

## Recorrido

```text
Pregunta empresarial
  → ficha de decisión
  → evidencia local disponible o pregunta faltante
  → análisis adecuado
  → revisión crítica
  → respuesta ejecutiva
  → tarea o siguiente pregunta
```

La revisión puede devolver el flujo a evidencia o a una pregunta; no puede
inventar un dato para terminar rápido.

## Reglas de seguridad y experiencia

- La base local sigue siendo la autoridad; las carpetas compartidas solo aportan
  documentos ordinarios.
- Las rutas de archivos, valores innecesarios y cadenas internas no aparecen en
  la respuesta ejecutiva.
- La revisión es interna por defecto. El empresario ve únicamente evidencia,
  límites y la razón de la siguiente pregunta.
- Una situación simple usa el recorrido mínimo; no activa E45.
- El sistema no crea perfil psicológico de personas desde un transcript.

## Pruebas de valor

1. **Cash:** un workbook con periodo incorrecto o suma inconsistente no genera
   una recomendación definitiva.
2. **Weekly:** dos reuniones que se contradicen se muestran como conflicto con
   la pregunta necesaria para resolverlo.
3. **Strategy:** una promesa de marca sin evidencia de cliente se detiene y
   pregunta por evidencia.
4. **Execution:** prioridades sin Critical Number no se convierten en tareas
   como si estuvieran listas.

## Decisiones de diseño

- No se crea un motor general de razonamiento; se extienden los flujos actuales.
- El contrato relevante es la respuesta de negocio, no la cadena de pensamiento.
- Los casos validan propiedades: evidencia, límites, pregunta y acción; no una
  redacción idéntica.
- E43 no actualiza confianza ni aprende del resultado. Ese cambio se reserva a
  E44 para no confundir buena explicación con efectividad real.
