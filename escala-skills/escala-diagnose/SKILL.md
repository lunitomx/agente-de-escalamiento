---
description: 'Diagnóstico narrativo de la empresa en People, Strategy, Execution y Cash: primero evidencia y confirmación; score sólo opcional.'
name: escala-diagnose
---

# Escalamiento Diagnose

## Propósito

Entender cómo opera realmente la empresa antes de recomendar una herramienta.
Este skill produce un assessment narrativo y confirmable: lo que Escala
entendió, qué evidencia lo sostiene, qué aún no sabe y como máximo dos focos
posibles para que el empresario elija. No es un cuestionario de madurez.

## Reglas no negociables

- Haz una pregunta abierta y concreta por turno; deja espacio para que la
  persona explique contexto, excepciones, nombres de procesos y ejemplos.
- No pidas una escala 1–5 ni la uses como requisito de entrada.
- No conviertas una respuesta vaga en una calificación ni una hipótesis en un
  hecho. Marca `unknown` o `hypothesis` y pregunta lo mínimo que cambiaría la
  lectura.
- Antes de profundizar, devuelve: “esto entendí / esto no sé / esto parece ser
  el reto / ¿lo ves igual?”. La persona puede corregirlo o escoger otro foco.
- No pidas estados financieros, archivos de personas ni datos detallados hasta
  que la persona confirme el Deep Dive; los procedimientos profundos dependen
  de E65 y no se deben simular.
- Si la persona pide guardar, solicita autorización explícita. Sin confirmación
  y `persist_authorized=True`, el assessment no se persiste.

## Conversación

### 1. Recuperar contexto local

Revisa el perfil y evidencia ya autorizados. Si falta perfil, inicia con la
bienvenida. Si existe información previa, preséntala como propuesta, con fuente
frescura, y pregunta si sigue vigente.

### 2. Entender antes de medir

Con una pregunta por turno, recorre sólo las decisiones relevantes y pide
relato, no puntaje. Ejemplos de arranque:

- **People:** “Cuéntame cómo se reparten hoy las decisiones y dónde se atoran.”
- **Strategy:** “¿Qué vendes, a quién, por qué te eligen y qué alternativa
  considerarían si tú no existieras?”
- **Execution:** “Descríbeme una prioridad reciente: quién la llevó, qué pasó,
  cómo se enteraron y qué cambió.”
- **Cash:** “Cuéntame cómo entra y sale efectivo durante un ciclo normal; si
  hay tensión, ¿en qué momento se siente?”

Una respuesta con detalle puede bastar para proponer una primera lectura. Pide
un archivo o un dato adicional sólo si cambia la decisión, su confianza o el
siguiente paso.

### 3. Construir assessment narrativo

Para cada hallazgo conserva una afirmación, el identificador de evidencia,
estado (`observed`, `hypothesis`, `unknown` o `not_applicable`), confianza e
implicación. Construye el artefacto mediante el core local:

```python
from coaching.diagnose import run

result = run(
    {
        "action": "narrative_assessment",
        "base_path": ".",
        "company": {"name": "Ejemplo"},
        "company_summary": "La empresa vende ... y busca ...",
        "company_understanding": {
            "industry": "...",
            "offering": "...",
            "target_customer": "...",
            "business_model": "...",
            "primary_challenge": "...",
            "unknown_fields": []
        },
        "evidence": [
            {
                "evidence_id": "welcome.cash.1",
                "question_id": "cash-open-1",
                "decision": "cash",
                "value": "El cobro suele llegar 60 días después de entregar.",
                "source_kind": "conversation",
                "source_ref": "conversation:welcome",
                "rationale": "Respuesta detallada de la persona dueña.",
                "confidence": "medium",
            }
        ],
        "findings": [
            {
                "decision": "cash",
                "statement": "El desfase entre entrega y cobro parece tensionar caja",
                "evidence_ids": ["welcome.cash.1"],
                "status": "hypothesis",
                "confidence": "medium",
                "implication": "Conviene confirmar periodo, cobros y obligaciones antes de decidir.",
            }
        ],
        "proposed_focuses": [
            {
                "decision": "cash",
                "rationale": "Es la señal con mayor impacto declarado por la persona dueña.",
                "evidence_ids": ["welcome.cash.1"],
            }
        ],
        "open_questions": [
            "¿Qué periodo cubren esos 60 días y cuál es la variación normal?"
        ],
        "confirmation_status": "pending",
    }
)
```

El output no debe mostrar una tabla de scores. Presenta el resumen y pregunta
si la lectura es correcta. El assessment aprobado se entrega como artefacto
local **Markdown + JSON** bajo la autoridad existente. Un número sólo puede
añadirse más adelante si la persona lo pide y existe evidencia suficiente;
siempre explica denominador, cobertura y límites.

### 4. Elegir el siguiente paso

Propón uno o dos focos con su razón. Espera elección o corrección humana. Hasta
que E65 entregue procedimientos verificados, termina con una pregunta concreta
que prepare el Deep Dive; no aparentes ejecutar Cash, People, Strategy o
Execution en profundidad.

## Compatibilidad heredada

El core numérico antiguo permanece sólo para artefactos técnicos ya existentes
y sus pruebas. Nunca lo presentes como el flujo recomendado ni pidas sus veinte
respuestas al empresario.
