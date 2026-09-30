---
epic_id: E71
title: Inteligencia de mercado, competencia y customer journey
status: planned
jira_key: "ESCALA-35"
depends_on: [E49, E55, E67]
---

# Scope E71

## Objetivo

Dar a ESCALA una capacidad de investigación estratégica que, después de
confirmar el modelo de negocio, produzca evidencia fechada sobre mercado,
competencia, prospectos o customer journey y la convierta en decisiones locales
revisables.

## Dentro

- Perfil de investigación con oferta, ICP, geografía, segmento, unidad monetaria,
  horizonte, pregunta y datos que el usuario autorizó compartir en la consulta.
- Fichas de fuente: URL/título/fecha de consulta, fecha de publicación si existe,
  cobertura, extracto breve, afirmación respaldada y calidad/limitación.
- Modelos explícitos de TAM/SAM/SOM y alternativas cuando sólo exista evidencia
  parcial; rango y supuestos en vez de falsa precisión.
- Mapa de competidores y prospectos con clasificación, diferenciación observada,
  evidencia y preguntas pendientes.
- Customer journey como hipótesis de etapas, intentos, fricciones, evidencia y
  experimento de validación.
- Brief local versionado, revisión programada sugerida y handoff a Strategy,
  Execution, Cash o dashboard advisor.
- Trigger/non-trigger para `strategy-analyst`; puede pedir research, pero
  `escala` conserva la síntesis, el consentimiento y la escritura de estado.

## Fuera

- Conectores OAuth, scraping masivo, rastreo automático recurrente o perfilado
  de personas.
- Enviar documentos corporativos completos, estados financieros o PII a la web.
- Declarar un competidor, un precio o un tamaño sin fuente/fecha/metodología.
- Persistir datos externos como hechos de empresa sin aprobación humana.

## Dependencias y secuencia

```text
E49 comprensión inicial + E55 hechos locales
          ↓
S71.1 contrato → S71.2 confirmación → S71.3/S71.4/S71.5 investigación
                                                ↓
                                      S71.6 brief/handoff → S71.7 evals
```

E67 instala el perfil Strategy que solicita la capacidad. E73 consume briefs
aprobados para sugerir dashboards; E75 los usa para elegir un deep dive.

## Criterios de terminación

- Cada output conserva pregunta, encuadre confirmado, fuentes, fecha y estado
  `fact-external`, `hypothesis`, `unknown` o `company-confirmed`.
- Un tamaño de mercado no se muestra como un número único sin método, rango o
  limitación explícita.
- Competidores no confirmados permanecen como candidatos y se pueden corregir.
- El customer journey conserva evidencia de primera mano versus inferencia.
- Casos de fuente antigua, conflicto, falta de datos y datos sensibles pasan.
- La capacidad funciona detrás de `escala` sin crear un comando público nuevo.

## Riesgos y guardrails

| Riesgo | Mitigación |
|---|---|
| Investigación convincente pero obsoleta | freshness, fecha de revisión y fuentes a la vista. |
| TAM irrelevante para el negocio real | confirmación de segmento/geografía/ICP antes de cálculo. |
| Competidores “alucinados” | URL, razón de inclusión y estado candidato hasta confirmación. |
| Fuga de datos de empresa | paquete mínimo de consulta y bloqueo de adjuntos sensibles. |
