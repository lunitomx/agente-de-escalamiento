---
epic_id: "E45"
title: "Specialist Team on Demand"
status: "planned"
depends_on: ["E42", "E43", "E44"]
created: "2026-07-23"
---

# E45 — Especialistas bajo demanda

## Hipótesis

Para un empresario que enfrenta un problema que cruza varias decisiones, un
equipo pequeño de especialistas con un crítico y un verificador detecta riesgos
que un solo análisis puede pasar por alto, sin obligarlo a leer un debate interno.

A diferencia de ejecutar muchos agentes por costumbre, ESCALA solo activa este
equipo cuando el problema, la evidencia y el posible impacto justifican el
tiempo adicional.

## Métricas de éxito

- **Señal temprana:** el router deja las preguntas simples con un solo coach y
  activa especialistas únicamente en casos que cumplen criterios de complejidad.
- **Resultado:** empresarios consideran superior la recomendación compleja frente
  a la línea base de un solo análisis.
- **Guardrail:** el verificador bloquea conclusiones sin fuente y los desacuerdos
  quedan explícitos, no escondidos.

## Tamaño

M — seis historias, con un caso transversal Cash + Execution antes de ampliar
a People y Strategy.

## Dentro

- Clasificar una pregunta como simple o compleja.
- Elegir especialistas por la decisión a la que realmente aportan.
- Revisar supuestos, cifras, fuentes y desacuerdos.
- Sintetizar una sola recomendación ejecutiva.
- Establecer límites de tiempo, rondas y contexto compartido.

## No-Gos

- No ejecutar especialistas para toda conversación.
- No convertir roles en personajes decorativos.
- No dar todo el historial empresarial a cada especialista.
- No permitir que un especialista apruebe una decisión humana.
- No cambiar skills o código; corresponde a E46.

## Rabbit Holes

- Medir éxito por cantidad de roles o texto producido.
- Hacer una votación promedio que esconda incertidumbre.
- Requerir concurrencia técnica cuando una revisión secuencial produce el mismo
  valor local.
- Copiar datos a un servicio central para coordinar especialistas.
