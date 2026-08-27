---
epic_id: "E45"
title: "Equipo instalado de cuatro especialistas bajo demanda"
status: "planned"
depends_on: ["E44", "E49"]
created: "2026-07-23"
---

# E45 — Equipo instalado de cuatro especialistas bajo demanda

## Hipótesis

Para un empresario que enfrenta un problema que cruza varias decisiones,
ESCALA instala cuatro especialistas —Cash, Execution, People y Strategy— y los
activa sólo cuando aportan evidencia o una perspectiva que el coach principal
no debe improvisar. El empresario sigue hablando con un solo agente y no lee
un debate interno.

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
- Instalar y versionar cuatro perfiles: `cash-analyst`,
  `execution-operator`, `people-coach` y `strategy-analyst`.
- Elegir uno o dos especialistas por la decisión a la que realmente aportan.
- Revisar supuestos, cifras, fuentes y desacuerdos.
- Sintetizar una sola recomendación ejecutiva.
- Establecer límites de tiempo, rondas y contexto compartido.

## No-Gos

- No ejecutar los cuatro especialistas para toda conversación.
- No dejar bots autónomos corriendo tras el Welcome; se instalan definiciones,
  no procesos permanentes.
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
