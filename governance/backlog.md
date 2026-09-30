# Backlog canónico — ESCALA

> **Actualizado:** 2026-09-12 — reparación del piloto E78–E81
> **Repositorio canónico privado:** `https://github.com/lunitomx/agente-de-escalamiento`
> **Regla:** un estado sólo puede ser `complete` si su alcance, evidencia y
> aceptación exigida coinciden. Una suite verde no sustituye una aceptación
> humana ni una plataforma limpia cuando el contrato las exige.

## Cómo leer este backlog

- **Activo:** se puede ejecutar ahora; cada historia debe seguir el ciclo RaiSE
  de diseño, implementación, verificación, revisión y cierre honesto.
- **Planificado:** alcance documentado e implementación no iniciada. Las
  historias sin bloqueo pueden pasar a diseño; las demás esperan sus dependencias.
- **Revisión requerida:** existe una entrega histórica, pero la instalación o
  la evidencia actual no la reproduce aún.
- **No se usa `done` como estado.** Los cierres terminales se rigen por
  [`closure-dispositions.yaml`](closure-dispositions.yaml).

El detalle de identidades legadas y decisiones de auditoría está en
[`epic-portfolio.md`](epic-portfolio.md). La autoridad de estado entre scope y
documentos históricos está en [`epic-state-authority.md`](epic-state-authority.md).
Los archivos históricos no formalizados no son trabajo activo sólo por existir
en `work/epics/`.

## Prioridad de ejecución

La auditoría del 2026-09-12 añade un carril prioritario de reparación antes de
ampliar el piloto. [Programa, hallazgos, 24 historias y gates](pilot-readiness-2026-09-12.md).
Los objetivos de adopción son propuestas para el piloto, no resultados observados.

| Orden | Épica | Estado real | Por qué va ahora | Gate para avanzar |
|---:|---|---|---|---|
| R1 | [E78 — Instalación, runtime y recuperación](../work/epics/e78-reliable-installation-runtime-recovery/scope.md) | planned; primera historia diseñable | Lanzador fuera de `.venv`, actualización sin plataforma y health por marker reproducidos. | Artefacto real instala, ejecuta, actualiza y recupera estado; recibos para E42. |
| R2 | [E79 — Aislamiento, privacidad y seguridad](../work/epics/e79-company-isolation-privacy-local-security/scope.md) | planned; contrato/HTTP diseñables | Cruce de empresas, límite static incorrecto y promesa de privacidad incompleta. | Cero cruces o filtraciones en integración; legado y consentimiento preservados. |
| R3 | [E80 — Diagnóstico e intake confiables](../work/epics/e80-evidence-backed-diagnostics-document-intake/scope.md) | planned; semántica diseñable | Placeholders producen 100/good; PDF nativo no disponible y falta calificar contexto/continuidad. | Indicadores honestos, PDF textual/fallback y primera acción sustentada recuperable. |
| R4 | [E81 — Piloto y soporte](../work/epics/e81-entrepreneur-pilot-qualification-support/scope.md) | planned; preparación posible | Falta observar autonomía y costo de soporte en dos cohortes separadas. | E78–E80 verificadas → 3–5 acompañados → 20; aceptación real, sin sustituir E42/E68. |
| R | E41 — Lifecycle local | active; reabierta por H05 | El estado healthy no comprueba aplicación/proceso; E78 posee la reparación para evitar duplicación. | Recualificar requisitos afectados con evidencia de proceso y recuperación reales. |
| 0 | E10 — Distribución portable | active; reparación E78 y gate externo E42/E68 | S10.10/S10.11 son entregas históricas; el lanzador y update actuales requieren reparación adicional. | E78 verifica el recorrido y E42/E68 registran aceptación externa. |
| G | E42 — Qualification y catálogo verdadero | Gate externo de release; paralelo | Aún faltan 6 requisitos de aceptación maestra, que requieren hardware limpio y aceptación humana; consumirá el bundle corregido de E10. | 42/42 requisitos con recibos reproducibles y aprobación humana; no se sustituyen por fixtures. |
| 1 | E44 — Aprendizaje de resultados | En curso local; aceptación pendiente | La cadena decisión→acción→resultado→aprendizaje está calificada sintéticamente en cuatro pilares. | Retrospectiva y aceptación real del empresario, sin atribución causal inventada. |
| 2 | E45 — Especialistas internos | En curso local; piloto pendiente | Contratos, router, contexto mínimo, crítico y verificador están calificados; falta demostrar valor real. | Comparación honesta con coach único, piloto empresarial y empaquetado E67. |
| 3 | E60–E63 — Fidelidad por dominio | En curso; gates de fuente delimitados | People/Strategy/Execution esperan inspección visual autorizada; Cash conserva CASh como herramienta source-bounded y espera revisión independiente de sus candidatos. | Cero hallazgos críticos abiertos y evidencia fuente suficiente antes de E64. |
| 4 | E64 — Consolidación ontológica | Planificado; bloqueado por E60–E63 | Sólo consolida candidatos aprobados, no texto crudo ni fórmulas bloqueadas. | Cobertura de estructuras nombradas, evidencia normativa total y cero relaciones rotas. |
| 5 | E65 + E67 + E68 | Planificado; secuencia posterior | Procedimientos MVP, empaquetado portable y equivalencia Codex/Claude consumen E64. | Contratos, activación/no-activación y golden cases semánticamente equivalentes. |
| 6 | E75 (S75.1/S75.2) | En curso local | Assessment narrativo, confirmación y consentimiento se reparan ya con E49/E55; Deep Dives siguen esperando E65. | No hay escala 1–5 como entrada y ningún handoff se simula. |
| 7 | E69, E71–E75 + E77 | Planificado por olas | Biblioteca base, research, Cash Learning Day, dashboards, workspace, packs privados de cursos y handoffs se abren tras el núcleo portable. | Cada ola conserva procedencia, privacidad, aceptación y pruebas. |
| 8 | E46 + E70 | Planificado | Mejora gobernada sólo con resultados reales; release sólo con todos los gates. | Aprobación/rollback y aceptación final honesta. |
| — | E76 — Recuperación reproducible de RaiSE | Completada | Manifest, configuración mínima y grafo ya se recuperaron sin venv duplicado. | No reabrir salvo regresión reproducible propia. |
| — | E47, E49, E51, E52, E55, E56, E57–E59 | Completadas | Son contratos verificados que las épicas activas pueden consumir. | No reabrir salvo regresión propia demostrada. |

Las reparaciones E78–E80 tienen propietario exclusivo. E73 consume la semántica
de indicadores E80 y E74 consume el aislamiento local E79; sus extensiones
futuras no retrasan la reparación urgente. E70 incorpora E81 como entrada de
decisión de distribución. El conteo histórico 36/42 de E37–E42 no certifica la
regresión reabierta de E41: sus requisitos afectados deben recualificarse.

## Núcleo de conocimiento y distribución

Estas épicas materializan el corpus verificable de Scaling Up. Se ejecutan en
orden, después de E42/E49/E55 cuando el producto tenga una línea base fiable:

**Prerrequisitos ya satisfechos:** E52 aporta persistencia local consentida de
Welcome; E56 aporta la única puerta pública `escala` y el catálogo canónico.
No deben reabrirse para iniciar E57–E75 salvo que una prueba de regresión
demuestre una falla propia.

| Ola | Épicas | Resultado |
|---|---|---|
| Fuente | E57 | Manifiesto de fuentes, autoridad y procedencia. |
| Modelo | E58, E59 | Ontología compatible y fundamentos 4D fieles. |
| Cobertura | E60, E61, E62, E63, E64 | People, Strategy, Execution y Cash transformados en nodos trazables. |
| Procedimientos | E65, E69 | Intervenciones completas con entradas, reglas, salida y evaluación. |
| Portabilidad | E67, E68 | Un núcleo portable para Codex/Claude, con adaptadores aislados y empaquetado Agent Plugins v1 sin MCP implícito. |
| Release | E70 | Instalación limpia, paridad, límites y distribución honesta. |

## Decisiones de arquitectura ya tomadas

1. **Un solo agente visible: `escala`.** El empresario no navega cuatro bots
   ni cuatro comandos.
2. **Cuatro especialistas privados:** `cash-analyst`, `execution-operator`,
   `people-coach` y `strategy-analyst`. Se invoca sólo el que aporta; el
   orquestador conserva el contexto, pide autorización cuando la acción la
   requiere y entrega una única recomendación.
3. **Los skills son procedimientos; los especialistas son roles.** No se crea
   un subagente por cada herramienta ni un quinto bot de research.
4. **Memoria portable por empresa:** Markdown/YAML versionado como fuente
   compartible; SQLite local como caché/índice, nunca como archivo sincronizado.
5. **Automatización sugerida, no impuesta:** pulse semanal, revisión SWT o
   investigaciones periódicas se proponen con propósito, datos y frecuencia;
   la persona acepta antes de activarlas.
6. **Datos delicados:** se detectan, se advierte y no se persisten/indexan sin
   autorización explícita.

## Definition of done transversal

Una historia no se cierra hasta que tenga: alcance explícito, implementación,
prueba positiva y negativa, evidencia con procedencia, documentación para el
empresario, verificación independiente cuando aplique y retrospectiva. Si falta
una condición externa (hardware o aceptación humana), la historia permanece
activa o en revisión; no se completa por sustitución sintética.
