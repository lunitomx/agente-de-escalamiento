# Design E71 — Research como capacidad de Strategy, no como bot adicional

## Decisión de arquitectura

El equipo instalado mantiene cuatro perfiles. Cuando `strategy-analyst` detecta
una pregunta que requiere actualidad externa, solicita la capacidad `research`
mediante un contrato estructurado. `escala` confirma el encuadre, entrega el
paquete mínimo y recibe un brief con evidencia; no se instala un quinto chat.

```text
usuario → escala → confirma encuadre
                    ↓
             strategy-analyst
                    ↓ solicita research con datos mínimos
        fuentes fechadas → verificador de citas
                    ↓
        brief local → escala → usuario confirma / decide / profundiza
```

## Modelo de datos mínimo

- `ResearchRequest`: pregunta, empresa, segmento, geografía, ICP, límites de
  datos, fecha y owner.
- `ResearchClaim`: afirmación, tipo, fuente, fecha de consulta, evidencia,
  confianza, limitación y estado.
- `MarketEstimate`: TAM/SAM/SOM, definición, moneda, periodo, método, rango,
  supuestos y claims soporte.
- `JourneyHypothesis`: etapa, necesidad, touchpoint, fricción, evidencia,
  confianza y experimento.
- `ResearchBrief`: síntesis, decisiones, preguntas, vencimiento y handoffs.

## Reglas de decisión

- Sin segmento/geografía confirmados: no se calcula mercado; se devuelve la
  pregunta que falta.
- Fuente que contradice a otra: se registran ambas y no se promedian.
- Afirmación externa no se vuelve `company-confirmed` sin aprobación explícita.
- Si una investigación pide datos sensibles, se reformula/minimiza o se detiene.
- El resultado sólo propone automatizar una revisión si el usuario acepta la
  periodicidad y el costo de mantenerla.

## Evaluación

Golden cases: SaaS B2B con cifras públicas, negocio local sin datos públicos,
mercado ambiguo, competidores contradictorios, prospecto puntual y documento
sensible que debe ser excluido. La evaluación revisa trazabilidad, actualidad,
calibración de incertidumbre y utilidad para una decisión, no longitud del
brief.
