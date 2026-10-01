---
description: 'Diagnóstico narrativo de la empresa en People, Strategy, Execution y Cash: primero evidencia y confirmación; score sólo opcional.'
name: escala-diagnose
---

# Escalamiento Diagnose

## Propósito

Entender cómo opera realmente la empresa antes de recomendar una herramienta.
Este skill produce un assessment narrativo y confirmable: lo que Escala
entendió, qué evidencia lo sostiene, qué aún no sabe y, ya confirmado, una
acción para esta semana con responsable y fecha. No es un cuestionario de
madurez.

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

Revisa también si el empresario ya investigó algo fuera de su empresa y tomó
una decisión (desde la raíz del proyecto):

```bash
echo '{"action": "diagnosis", "base_path": ".", "today": "2026-09-30"}' | python3 -m coaching.research
```

`diagnostic_inputs` trae, listo para los campos que el diagnóstico ya tiene:

- `evidence`: cada decisión que el empresario confirmó al cerrar una
  investigación, como hecho local que apunta a su reporte guardado. Úsala como
  cualquier otra evidencia.
- `assumptions`: lo que dicen fuentes de fuera, con su estado y mes. Pásalo a
  `assumptions` del diagnóstico; nunca como hecho.
- `open_questions`: lo que la investigación no encontró y el dato que el
  empresario quedó en conseguir. Pásalo a `open_questions`.

Haz lo mismo con lo que decidió sobre cómo llega un cliente hasta que le
compra:

```bash
echo '{"action": "diagnosis", "base_path": ".", "today": "2026-09-30"}' | python3 -m coaching.journey
```

Trae los mismos tres campos y se usa igual: su decisión como hecho local,
los supuestos en `assumptions` y lo que falta en `open_questions`.

Si `refresh_offers` no viene vacío (una investigación pasó su fecha de
revisión), di primero ese `message` y espera su respuesta: la evidencia vencida
entra `stale` y con confianza baja. Si no hay nada guardado, sigue sin
mencionarlo.

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
            "unknown_fields": [],
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

### 4. Cerrar con una acción de esta semana

El diagnóstico no termina preparando otra sesión: termina con **una** acción
que el empresario puede hacer esta semana. Primero presenta la lectura y espera
su "sí" o su corrección (`confirmation_status: "pending"`). Con la lectura
confirmada o corregida, elige **un** foco (el freno principal) y vuelve a
llamar al core con `confirmation_status` en `confirmed` o `corrected`, `today`
(la fecha de hoy, `AAAA-MM-DD`) y `weekly_action`:

```python
"weekly_action": {
    "decision": "cash",
    "constraint": "Tu freno principal es que cobras a 60 días.",
    "action": "llama a tus 3 clientes más grandes y pide pago a 30 días.",
    "responsible": "tú",
    "due": "2026-10-09",
    "evidence_ids": ["welcome.cash.1"],
},
"sheet_offer_made": False,
```

- `constraint` es una sola oración. `responsible` es "tú" salvo que el
  empresario diga quién lo hará. `due` va en `AAAA-MM-DD` y cae entre hoy y
  7 días; al empresario el core se la dice en palabras.
- **Nunca inventes números.** Cada número de la acción tiene que estar en la
  evidencia que cita; si no, el core la rechaza. Si falta el dato, la acción es
  conseguirlo ("junta cuánto te debe cada cliente y desde cuándo").
- Di el `output` tal cual; es el último mensaje del diagnóstico. Por ejemplo:

> Tu freno principal es que cobras a 60 días. Esta semana: llama a tus 3
> clientes más grandes y pide pago a 30 días. Responsable: tú. Fecha: viernes 9
> de octubre. ¿Lo anoto como compromiso en tu hoja?

- La oferta de la hoja va **una sola vez** por conversación. Si ya la hiciste,
  o dijo "después" o "no", manda `"sheet_offer_made": True`: el cierre queda
  con la acción, el responsable y la fecha, sin volver a preguntar. Si cambia
  de tema sin contestar, cuenta como "después".
- **Si dice que sí**, lo lleva `escala` con el especialista de execution a la
  hoja del grupo, con `artifacts.tracker_request`: es la llamada `propose` del
  tracker con la acción como fila de sus compromisos del mes. Si su pestaña aún
  no está confirmada, el tracker la busca primero. ESCALA no escribe en la
  hoja: propone la fila y el empresario la pega.

No aparentes ejecutar en profundidad dinero, equipo, estrategia o día a día:
la acción es un primer paso concreto, no la revisión a fondo.

Si el reto parece de Strategy (demanda, clientes, zona nueva) o de Cash por
precio o margen, y no hay una investigación vigente sobre eso, ofrécela al
presentar la lectura, antes del cierre (el cierre siempre es la acción):
"Si quieres, antes de decidir vemos cómo cobran negocios parecidos / cómo está
tu mercado, sin usar datos de tu empresa en las búsquedas". Si dice que sí, lo
lleva `escala` con el especialista de strategy. La elección de ruta automática
(E75 S75.3) aún no existe: no simules el traspaso ni digas que ya empezó la
investigación. En People o Execution no lo ofrezcas (el freno es interno).

## Compatibilidad heredada

El core numérico antiguo permanece sólo para artefactos técnicos ya existentes
y sus pruebas. Nunca lo presentes como el flujo recomendado ni pidas sus veinte
respuestas al empresario.
