---
epic_id: E73
title: Asesor adaptativo de dashboards de negocio
status: planned
depends_on: [E38, E40, E55, E65, E67]
owners: [escala, cash-analyst, execution-operator, people-coach, strategy-analyst]
---

# PRD E73 — Asesor adaptativo de dashboards de negocio

## Problema

ESCALA ya tiene visuales y puede producir reportes, pero aún no decide con el
empresario qué dashboard vale la pena construir, con qué evidencia y qué
pregunta empresarial responderá. El riesgo es generar paneles bonitos que no
cambian una decisión.

## Usuario y trabajo por resolver

Al terminar un diagnóstico, Learning Day o revisión, el empresario necesita que
ESCALA diga: “con la información que ya tenemos, estos son los dos paneles que
tendrían valor; éste es el que puedo construir hoy, éste necesita estos datos”.

## Resultado de producto

El orquestador y el especialista de la decisión preparan una recomendación de
dashboard basada en: decisión a tomar, owner, cadencia, métricas confirmadas,
calidad/freshness, visual apropiado y campos faltantes. El usuario acepta,
posterga o descarta. Sólo tras aceptar se genera un artefacto local.

## Principios

- Un dashboard responde una decisión concreta; no es un inventario de KPIs.
- Una métrica sin fuente, periodo o definición no llega a un visual ejecutivo.
- La recomendación es proactiva pero la construcción, persistencia y agenda de
  revisión requieren confirmación del usuario.
- Cada uno de los cuatro especialistas puede proponer un panel de su dominio;
  `escala` consolida y evita saturación.

## Historias

| ID | Historia | Resultado |
|---|---|---|
| S73.1 | Contrato de dashboard | Pregunta, audiencia, cadencia, métricas, fuentes, visual, límites y aceptación están tipados. |
| S73.2 | Motor de recomendación | Diagnóstico/artefactos generan propuestas explicables y priorizadas. |
| S73.3 | Feasibility y datos faltantes | El sistema distingue “generable”, “requiere datos” y “no recomendado ahora”. |
| S73.4 | Generación local aprobada | HTML/CSV/Markdown local con evidencia y fecha de actualización; sin dashboard hosteado. |
| S73.5 | Catálogo por decisión | Cash, Execution, People y Strategy tienen patrones, no plantillas obligatorias. |
| S73.6 | Evaluación | Casos sin datos, datos stale, panel redundante, aceptación/rechazo y dos empresas pasan. |

## Métricas de éxito

- Cada dashboard aprobado declara la decisión que facilita, owner y cadencia.
- Ningún visual usa métrica ambigua o vence silenciosamente.
- El usuario entiende qué no se puede generar todavía y por qué.
- Un dashboard no invade la conversación: como máximo se proponen dos a la vez
  salvo pedido explícito del usuario.

## Fuera

- BI hospedado, telemetría, conectores cloud o actualización autónoma.
- Una pantalla universal de indicadores sin contexto de negocio.
- Convertir la recomendación de dashboard en una calificación de empleados.
