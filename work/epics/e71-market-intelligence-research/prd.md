---
epic_id: E71
title: Inteligencia de mercado, competencia y customer journey
status: planned
depends_on: [E49, E55, E67]
owners: [strategy-analyst, escala]
---

# PRD E71 — Inteligencia de mercado, competencia y customer journey

## Problema

Después del Welcome, un empresario sabe qué vende pero no necesariamente cuánto
vale el mercado al que realmente puede servir, contra quién compite ni dónde se
pierde valor en el recorrido del cliente. Hoy ESCALA no puede convertir esa
comprensión inicial en una investigación fechada, verificable y accionable.

## Usuario y trabajo por resolver

Un dueño o líder dice: “entiendo mi empresa; ahora ayúdame a validar el mercado,
competidores, prospecto o customer journey”. Quiere una recomendación útil para
decidir qué investigar o mejorar, no una lista de resultados de búsqueda.

## Resultado de producto

`escala` confirma primero oferta, segmento, geografía, cliente y horizonte. Sólo
después activa la capacidad interna de research desde `strategy-analyst`, con
fuentes fechadas y una devolución ejecutiva que separa hechos, inferencias e
hipótesis locales.

El entregable contiene:

- TAM, SAM y SOM con definición, método, moneda, geografía, periodo y grado de
  confianza; si no se puede estimar, declara el hueco en vez de inventar monto.
- Mapa de competidores: directo, indirecto, sustituto y “por confirmar”, con
  evidencia, fecha de consulta y razón de inclusión.
- Hipótesis de customer journey, fricciones y preguntas de validación.
- Implicaciones para Strategy/Execution/Cash, una prioridad investigable y la
  recomendación de dashboard o Learning Day si corresponde.

## Principios

1. Investigación no es una verdad permanente: cada afirmación externa tiene
   URL/fuente, fecha, cobertura y fecha de revisión sugerida.
2. La empresa confirma el encuadre antes de que se anuncie tamaño de mercado o
   competidor; los supuestos se muestran de forma editable.
3. Research se activa bajo demanda o por propuesta aceptada, nunca como
   vigilancia autónoma persistente.
4. No se envían archivos financieros, datos personales ni secretos del cliente
   a una búsqueda externa.
5. Research es una capacidad interna, no un quinto miniagente visible.

## Historias

| ID | Historia | Resultado |
|---|---|---|
| S71.1 | Contrato de investigación | Pregunta, encuadre, fuentes, tiempo, evidencia, sensibilidad y vencimiento están tipados. |
| S71.2 | Confirmación de mercado | ESCALA devuelve su comprensión de oferta/cliente/geografía y pide corrección antes de investigar. |
| S71.3 | TAM/SAM/SOM honesto | Tamaños y método reproducibles o un “no estimable todavía” con siguiente evidencia requerida. |
| S71.4 | Competidores y prospectos | Matriz de alternativas/prospectos con evidencia, diferenciación y nivel de certeza. |
| S71.5 | Customer journey | Journey hipótesis→evidencia→fricción→pregunta/acción, sin afirmar que el usuario final fue entrevistado si no lo fue. |
| S71.6 | Research brief y memoria | Brief local, citas, vigencia, decisión/handoff y actualización sólo tras aprobación. |
| S71.7 | Calificación | Casos actuales, fuentes contradictorias, empresa sin mercado claro y datos sensibles pasan evaluaciones. |

## Métricas de éxito

- 100% de afirmaciones cuantitativas/competitivas llevan fuente y fecha, o son
  etiquetadas hipótesis.
- El usuario confirma/corrige el encuadre antes de un brief externo.
- Un brief genera al menos una pregunta, decisión o experimento verificable;
  no sólo texto descriptivo.
- Cero archivos confidenciales de empresa se transmiten por la capacidad.

## Fuera

- Scraping indiscriminado, monitorización continua, CRM/OAuth o compra de datos.
- Recomendación de inversión, valoración financiera definitiva o asesoría legal.
- Convertir cualquier página encontrada en evidencia de mercado confiable.
- Crear un quinto subagente persistente.
