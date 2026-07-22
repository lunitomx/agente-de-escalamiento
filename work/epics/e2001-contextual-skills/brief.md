# Epic Brief: E20 — Contextual Skills (Grafo → Dashboards)

## Visión
Conectar los skills y dashboards existentes de Escala al grafo de conocimiento del libro. Cuando un coach abre el Power of One, puede pedir "contexto de Harnish" y el dashboard muestra la teoría relevante.

## Por qué separada
E19 crea el dato. E20 lo consume. Separarlas evita mezclar el pipeline de ingesta con la integración en skills.

## Lo que NO es
- No ingesta nuevo conocimiento (E19)
- No crea el board member (E21)
- No modifica la estructura del grafo

## Deliverables
- Cada dashboard puede consultar contexto relevante del grafo
- Skills de coaching pueden llamar a la knowledge API
- Panel lateral de "Contexto del libro" en dashboards
