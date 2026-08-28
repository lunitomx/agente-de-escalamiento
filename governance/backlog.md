# Backlog canónico — ESCALA

> **Auditado:** 2026-08-27
> **Repositorio canónico privado:** `https://github.com/lunitomx/agente-de-escalamiento`
> **Regla:** un estado sólo puede ser `complete` si su alcance, evidencia y
> aceptación exigida coinciden. Una suite verde no sustituye una aceptación
> humana ni una plataforma limpia cuando el contrato las exige.

## Cómo leer este backlog

- **Activo:** se puede ejecutar ahora; cada historia debe seguir el ciclo RaiSE
  de diseño, implementación, verificación, revisión y cierre honesto.
- **Planificado:** alcance aprobado, pero aún no debe iniciarse porque depende
  de un gate anterior.
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

| Orden | Épica | Estado real | Por qué va ahora | Gate para avanzar |
|---:|---|---|---|---|
| 0 | E10 — Distribución portable corregida | Reparación local completa; gate externo E42/E68 | El export portable no depende del checkout, verifica manifest, publica sólo `escala` y exige plataforma explícita; el runtime usa `.venv`/`uv`, no pip global. Faltan hardware limpio y modelos reales. | E42/E68 registran la aceptación externa sin sustituirla por fixtures. |
| G | E42 — Qualification y catálogo verdadero | Gate externo de release; paralelo | Aún faltan 6 requisitos de aceptación maestra, que requieren hardware limpio y aceptación humana; consumirá el bundle corregido de E10. | 42/42 requisitos con recibos reproducibles y aprobación humana; no se sustituyen por fixtures. |
| 1 | E44 — Aprendizaje de resultados | En curso local; aceptación pendiente | La cadena decisión→acción→resultado→aprendizaje está calificada sintéticamente en cuatro pilares. | Retrospectiva y aceptación real del empresario, sin atribución causal inventada. |
| 2 | E45 — Especialistas internos | En curso local; piloto pendiente | Contratos, router, contexto mínimo, crítico y verificador están calificados; falta demostrar valor real. | Comparación honesta con coach único, piloto empresarial y empaquetado E67. |
| 3 | E60–E63 — Fidelidad por dominio | En curso; gates de fuente delimitados | People/Strategy/Execution esperan inspección visual autorizada; Cash conserva CASh como herramienta source-bounded y espera revisión independiente de sus candidatos. | Cero hallazgos críticos abiertos y evidencia fuente suficiente antes de E64. |
| 4 | E64 — Consolidación ontológica | Planificado; bloqueado por E60–E63 | Sólo consolida candidatos aprobados, no texto crudo ni fórmulas bloqueadas. | Cobertura de estructuras nombradas, evidencia normativa total y cero relaciones rotas. |
| 5 | E65 + E67 + E68 | Planificado; secuencia posterior | Procedimientos MVP, empaquetado portable y equivalencia Codex/Claude consumen E64. | Contratos, activación/no-activación y golden cases semánticamente equivalentes. |
| 6 | E75 (S75.1/S75.2) | En curso local | Assessment narrativo, confirmación y consentimiento se reparan ya con E49/E55; Deep Dives siguen esperando E65. | No hay escala 1–5 como entrada y ningún handoff se simula. |
| 7 | E69, E71–E74 + E75 (S75.3–S75.6) | Planificado por olas | Biblioteca, research, Cash Learning Day, dashboards, workspace y handoffs se abren tras el núcleo portable. | Cada ola conserva procedencia, privacidad, aceptación y pruebas. |
| 8 | E46 + E70 | Planificado | Mejora gobernada sólo con resultados reales; release sólo con todos los gates. | Aprobación/rollback y aceptación final honesta. |
| — | E76 — Recuperación reproducible de RaiSE | Completada | Manifest, configuración mínima y grafo ya se recuperaron sin venv duplicado. | No reabrir salvo regresión reproducible propia. |
| — | E47, E49, E51, E52, E55, E56, E57–E59 | Completadas | Son contratos verificados que las épicas activas pueden consumir. | No reabrir salvo regresión propia demostrada. |

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
