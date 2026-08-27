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
[`epic-portfolio.md`](epic-portfolio.md). Los archivos históricos no
formalizados no son trabajo activo sólo por existir en `work/epics/`.

## Prioridad de ejecución

| Orden | Épica | Estado real | Por qué va ahora | Gate para avanzar |
|---:|---|---|---|---|
| P | E76 — Recuperación reproducible de RaiSE | Activo en paralelo; no bloquea producto | El entorno de desarrollo no tiene manifest/configuración/grafo reproducible. | `rai doctor` queda sin errores aplicables y el build del grafo es reproducible, sin crear un segundo venv ni sobrescribir `.raise` sin autorización explícita. |
| G | E42 — Qualification y catálogo verdadero | Gate externo de release; paralelo | Es la línea base honesta: hoy los 6 requisitos E42 no tienen prueba maestra vigente. | Hardware limpio macOS/Windows, inventario probado de cada skill distribuido y aceptación humana registrada. |
| 2 | E47 — Workspace, OPSP y feedback | Completada | Producto re-verificado: workspace, OPSP y feedback local no requieren RaiSE. | 42 pruebas de producto; la reproducibilidad de RaiSE queda aislada en E76. |
| 3 | E49 — Experiencia diagnóstica y evidencia | Completada | El análisis inicial ya es narrativo, verificable y útil antes de profundizar. | Recibo local, ruta de 90 días y diagnóstico que distingue hechos, inferencias, N/A y preguntas materiales. |
| 4 | E55 — Onboarding multifuente y conciliación | Completada; GitHub #9 | Corrigió el Welcome para reutilizar hechos locales y distinguir evidencia faltante o incompatible. | Recibo sintético E55, 4 rutas adaptativas y conciliación conservadora probados. |
| 5 | E75 — Diagnóstico adaptativo y deep dive | Planificado | Convierte el diagnóstico en una ruta elegida por el empresario, no una batería de 1–5. | Handoff mínimo y explicable a Cash/Strategy/People/Execution. |
| 6 | E72 — Cash Learning Day | Planificado | Permite pedir el Excel/documentos adecuados y facilitar Cash a detalle. | Artefactos financieros, preguntas de conciliación y decisiones de 90 días. |
| 7 | E71 — Inteligencia de mercado | Planificado | Amplía Strategy con mercado, competidores, ICP y customer journey verificables. | Research fechado, fuentes visibles y revisión explícita del dueño. |
| 8 | E73 — Asesor de dashboards | Planificado | Sugiere visuales de negocio sólo cuando existe evidencia suficiente. | Dashboard recomendado, trazable, sin inventar métricas. |
| 9 | E74 — Workspace compartido multiempresa | Planificado | Hace colaboración por carpeta compartida sin volver SQLite sincronizado en autoridad. | Markdown/YAML compartido, conflictos explícitos y SQLite sólo como caché local. |
| 10 | E43 — Ciclo de coaching confiable | Completo localmente; gate E42 | Convierte evidencia en una respuesta ejecutiva antes de sumar más automatización. | Casos positivos/negativos verificados; falta solo la aceptación externa de E42 para release. |
| 11 | E44 — Aprendizaje de resultados | Planificado | Guarda decisión, resultado y aprendizaje confirmado, no “memoria” inventada. | Estado versionado y retrospectiva trimestral controlada. |
| 12 | E45 + E67 — Especialistas internos y adaptadores | Planificado | Instala Cash, Execution, People y Strategy bajo un solo orquestador. | Una puerta pública, contratos privados, rutas simples rápidas y casos transversales evaluados. |
| 13 | E46 — Mejora de producto gobernada | Planificado | Sólo se habilita tras datos de resultados y feedback aprobado. | Cambios propuestos, evaluados y aprobados; nunca mutación autónoma. |

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
| Portabilidad | E67, E68 | Un núcleo portable para Codex/Claude, con adaptadores aislados. |
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
