---
epic_id: E86
title: ESCALA para el dueño — un minuto, una puerta, una decisión
status: active
jira_key: "ESCALA-68"
closure_disposition: active
created: 2026-09-30
updated: 2026-10-15
depends_on: []
related: [E82, E83, E84, E85]
source: work/audits/escala-52-auditoria-usuario-final.md
---

# Scope E86

## Objetivo

Que un dueño no técnico reciba su primera recomendación accionable en 3 pasos o menos, sin jerga, en la
plataforma que ya usa. Nace de la auditoría ESCALA-52 (scorecard: primer minuto y paridad en rojo).

## Decisión del dueño (2026-09-30)

- Abrir esta épica con las historias propuestas en §4 de la auditoría.
- **Todo el grupo de accountability hará las pruebas** con usuarios reales (guion §5 de la auditoría).

## Decisión del dueño (2026-10-15) — Cash completo

- Cash crece dentro de esta épica con lo que enseñó el curso de cash (versión 2026-10-14).
  Se agregan S86.13–S86.31 (ola 5, S86.28–31, espera a 3 dueños reales). Plan completo: `plan-cash-curso-v2.md`.
- Cada dueño fija sus límites ideal/regular/malo; ESCALA le pregunta. Los del curso son ejemplo.
- Los 4 capítulos del flujo llevan una 5ª fila, «salidas de capital».
- ESCALA nunca inventa ni supone números: calcula el código con pruebas, no el modelo.

## Historias

Numeradas en el orden sugerido por la auditoría (baratas y visibles primero; la medición real a la mitad
para no invertir a ciegas en instalación y paridad).

| Historia | Jira | Entrega (hallazgos) | Tam. | Criterio verificable | Estado |
|---|---|---|:---:|---|---|
| S86.1 | ESCALA-69 | Cero comandos visibles (Q2 + Q4) | 2 | `grep '/escala-' escala-skills/*/SKILL.md` = 0 salvo `escala`, con test; `update.sh` deja 1 skill `escala*` | done |
| S86.2 | ESCALA-70 | Lenguaje del dueño (Q1 + A5) | 3 | Test sobre textos del dueño falla con People/Strategy/Execution/Cash/CCC/BHAG/SWT/OPSP/Deep Dive sin traducción | done |
| S86.3 | ESCALA-71 | Errores con salida (A1 + A2) | 3 | Test por módulo con fallo simulado; ningún `message` dice "tu Claude" | done |
| S86.4 | ESCALA-72 | Puerta que conoce todo (S2) | 5 | Cada procedimiento `keep` alcanzable desde una frase del dueño; "bajaron mis ventas" → Strategy | done |
| S86.5 | ESCALA-73 | Diagnóstico que termina en acción (S4) | 3 | Último mensaje con acción, responsable y fecha + oferta de anotarlo en la hoja | done |
| S86.6 | ESCALA-74 | Prueba con dueños reales (§5) | 2 | Sesiones con el grupo, métricas llenas | kit listo — sesiones pendientes |
| S86.7 | ESCALA-75 | Hoja con menos pegado (Q3 + S3) | 5 | ≤1 pegado por sección; cero preguntas de fecha | planned |
| S86.8 | ESCALA-76 | Reunión proactiva (A3) | 3 | Con reunión en ≤3 días se ofrece una vez; "después" no se repite | done |
| S86.9 | ESCALA-77 | Instalación de un paso (S1 corto plazo) | 5 | Máquina limpia: ≤3 pasos, 0 decisiones técnicas | done |
| S86.10 | ESCALA-78 | Paridad y consentimiento (A4 + M2/M7 del spike) | 3 | Misma entrada y cierre en Claude y Codex, transcripciones guardadas | done (código; transcripciones reales pendientes, guion M7 en s86.10-story.md) |
| S86.11 | ESCALA-79 | Lo que enseñó el curso de Cash (fichas) | 3 | Cada ficha con crédito y frase; paquetes las llevan; puerta cita sólo lo que está en ellas | done |
| S86.12 | ESCALA-80 | Fichas de cash sin nombre del instructor | 2 | Cero menciones en archivos versionados; cita "Según el curso de cash que vimos" | done |
| S86.13 | ESCALA-81 | El poder del uno da el efectivo correcto | 3 | 7 palancas al centavo: flujo total 1,143,864.91; utilidad 1,010,740.66 | done |
| S86.14 | ESCALA-82 | ESCALA lee los estados como vienen | 5 | CONTPAQi y Aspel sintéticos completos; una prueba por falla A4 | done |
| S86.15 | ESCALA-83 | Cada cuenta en su caja y revisión R1–R11 | 5 | Mover una cuenta de caja cambia el resultado; acumulado nunca ×12 | done |
| S86.16 | ESCALA-84 | Una sola calculadora, que viaja con ESCALA | 5 | Prueba dentro del paquete; cero procedimientos que calculan con el modelo | done |
| S86.17 | ESCALA-85 | Escenario «analiza mis estados» de punta a punta | 5 | 3 entradas (completa, sin balance anterior, sucia); ningún número del modelo | done |
| S86.18 | ESCALA-86 | Panel «Tu contabilidad real» | 3 | Financiamiento = operación = 15,014,008.75; otras cuentas por renglones | planned |
| S86.19 | ESCALA-87 | Panel «Días y ciclo del dinero» | 3 | 36.08→46.97; 25.30→28.15; 24.31→19.59; sin IVA 40.49 | planned |
| S86.20 | ESCALA-88 | Panel «Las tres medidas» y los 4 capítulos | 5 | Cascada al centavo −3,705,245.84; 5ª fila contra C3/C4 | planned |
| S86.21 | ESCALA-89 | Tu perfil ideal, con tus límites | 5 | Sin límites pregunta; color sin redondear | planned |
| S86.22 | ESCALA-90 | Simulador de las 7 palancas | 5 | Vista mensual: precio nunca resta efectivo | done |
| S86.23 | ESCALA-91 | Precio contra volumen y descuento | 3 | Equilibrio 26.60%; «cálculo de ESCALA» rotulado | done |
| S86.24 | ESCALA-92 | Margen pre-tax, salario de mercado y devoluciones | 3 | 15.47%; F6.2 «no calculable» con negativos | done |
| S86.25 | ESCALA-93 | Las travesuras | 2 | Ajustada 5,463,710.03; solo montos del dueño | planned |
| S86.26 | ESCALA-94 | El recorrido con paneles y decisión | 3 | Recorrido Mi Empresa de estados a todos los paneles | planned |
| S86.27 | ESCALA-95 | Limpieza de duplicados de cash | 2 | Una sola definición por fórmula | planned |
| S86.28 | ESCALA-96 | Evaluación instantánea (ola 5) | 5 | En espera: 3 dueños reales | waiting |
| S86.29 | ESCALA-97 | Los 5 caminos para crecer (ola 5) | 3 | En espera | waiting |
| S86.30 | ESCALA-98 | Semana y trimestre (ola 5) | 3 | En espera | waiting |
| S86.31 | ESCALA-99 | Post-its con tu board (ola 5) | 3 | En espera | waiting |

## Fuera de alcance

- Adaptador de ChatGPT (lo decide E85 con las pruebas M1–M3 del dueño).
- Escritura directa en la hoja (depende de M4/P2).
- Rediseño de tableros HTML que no sean de Cash.
- Decisiones aplicadas (recomendación del plan, 2026-10-16): descuento combinado con nota del curso; documentos LP como el curso + pregunta al dueño.
- Cálculo de impuestos y cualquier recomendación fiscal (van al contador).
- Pronósticos de flujo a futuro (el curso no los enseña).

## Reglas heredadas

- Fixtures sintéticos; nunca datos reales del tracker, `.escala/` ni `.scaleup/`.
- Español llano con ejemplo real en todo lo que ve el dueño.
- Ningún comando nuevo para el dueño; la única puerta es `escala`.
