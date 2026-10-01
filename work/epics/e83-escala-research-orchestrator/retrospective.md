# E83: Orquestador de investigación — Retrospective

**Fechas:** 2026-09-30 · **Jira:** ESCALA-49 · **Historias:** 5 (S83.1–S83.5), todas mergeadas a main. Absorbe E71 (ESCALA-35).

## Qué entrega
El dueño pregunta en lenguaje natural ("¿cuánto cobra mi competencia?", "¿qué tan grande es mi mercado?",
"¿qué tendencias vienen?") y `escala` lo lleva al procedimiento interno `escala-strategy-research`.
Tres modos — `benchmark`, `mercado`, `fortalezas-tendencias` — elegidos por ESCALA según la restricción.
Cada hallazgo lleva fuente y fecha (≤90 días); "confirmado" sólo con 3 fuentes de publicadores distintos.
El tamaño de mercado es rango con método o "no estimable todavía", nunca promedio ni número solo.
La decisión confirmada entra al siguiente diagnóstico como hecho local; lo externo entra como supuesto,
sin URLs. Fortalezas y tendencias alimentan el SWT existente sin crear otro.

## Métricas
- Tests de `coaching/research/`: 0 → 238 (+ tests de procedimiento). Suite completa verde salvo 3 fallas ambientales conocidas.
- Catálogo: 63 → 64 procedimientos, 64 → 65 capacidades; ningún comando nuevo para el dueño.

## Qué salió bien
- Privacidad como test desde S83.1: lo que se revisa es exactamente lo que se envía (NFKC, invisibles, letras parecidas, cifras escaladas).
- Riesgo primero: S83.5 probó la costura con el diagnóstico antes de construir mercado y fortalezas.
- Decisiones del dueño (90 días, INEGI no principal, palabras de giro) llegaron a tiempo y se volvieron reglas con test.
- S83.4 corrió el flujo sintético completo de los tres modos, con y sin búsqueda.

## Qué mejorar
- La regla de "no recortar hallazgos" (S83.5) y la regla de giro (S83.3) se descubrieron implementando; leer los validadores del consumidor y probar el caso real del dueño en el plan.
- El pipeline engine sigue roto para este repo (A53); ciclo manual.
- Un agente se cortó por límite de uso; reanudar con contexto funcionó sin pérdida.

## Pendiente fuera del epic (requiere al dueño o prueba real)
- Chequeos manuales A y B en claude.ai/Desktop (búsqueda real y procedimiento completo con un dueño).
- Preguntas abiertas de S83.3: ¿INEGI no principal en código?, mantenimiento de la lista de giros, nombres hechos sólo de palabras de giro.
- Preguntas abiertas de S83.4: ¿sólo fortalezas-tendencias alimenta el SWT?, celdas "sin fecha" reusadas, renombrar `comparables_only_in_benchmark`.
- `test_e42_qualification` s42.4 parece inestable en corridas combinadas.
