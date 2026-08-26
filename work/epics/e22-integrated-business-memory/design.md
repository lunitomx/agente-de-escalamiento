# Design: E22 — Memoria Empresarial Integrada

## Gemba y hallazgos

| Componente | Estado real | Decisión E22 |
|---|---|---|
| install.sh | Copia coaching y conocimiento, no escala_server. | Distribuir el runtime de memoria y un bridge auditable. |
| escala_server CLI | Default global en directorio personal. | Resolver todas las rutas desde la raíz del proyecto. |
| migración E18 | Lee my-company; no cubre el perfil, conversación ni plan canónico actuales. | Migración explícita de los cuatro artefactos actuales e idempotencia. |
| SessionStart | Toma la primera compañía y facts por confianza. | Seleccionar la única compañía del proyecto y recuperar facts confirmados. |
| SessionClose | Persiste textos y cambios automáticamente. | Proponer y confirmar datos antes de persistirlos. |
| front door | Llama sólo a coaching.router.conversation. | Integrar bridge de memoria sin exponer infraestructura. |

No hubo resultados del grafo RaiSE: el índice está vacío. Se continuó con gemba
del código y de las pruebas existentes.

## Arquitectura objetivo

    frase natural
          |
          v
    scaleup-frontdoor
          |
          v
    coaching.router.conversation
          |
          +-- MemoryBridge(project_root)
                 |
                 +-- .scaleup/memory/escala.db
                 |     companies, sessions, memory_facts, entities,
                 |     relationships, changes_log
                 |
                 +-- migración idempotente desde YAML/Markdown
                 +-- inicio: contexto relevante y cambios
                 +-- cierre: candidatos confirmados y registro de sesión

El bridge reutiliza DAOs, MemoryEngine, GraphEngine y Session orchestrators de
E18. Adapta rutas, empresa y confirmación; no levanta el servidor HTTP para que
la memoria funcione.

## Contratos

| Operación | Entrada | Salida/invariante |
|---|---|---|
| ensure_memory | raíz del proyecto | base local válida o fallback explícito |
| migrate | perfil, conversación, plan, worksheets | mismo contenido una o N veces, sin duplicados |
| open_session | empresa única | sesión activa y contexto de máximo cinco facts confirmados |
| propose_memory | frase natural | candidatos separados de facts almacenados |
| confirm_memory | sí/no por candidato | sólo confirmados pasan a memory_facts y grafo |
| close_session | sesión activa | cambios, resumen y sesión cerrada |

## Secuencia de implementación

1. S22.1 define contratos, fixture de empresa y ADR.
2. S22.2 extrae un runtime por proyecto de los defaults globales de E18.
3. S22.3 migra YAML/Markdown actuales y prueba repetición/rollback.
4. S22.4 implementa inicio y recuperación con datos confirmados.
5. S22.5 implementa propuesta/confirmación y cierre.
6. S22.6 conecta el front door e instalador de los tres clientes.
7. S22.7 valida migración, aislamiento, continuidad y distribución.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Migración incompleta | Fixtures de perfil, plan parcial/completo, conversación y worksheets. |
| Datos falsos | Confirmación por candidato y fuente obligatoria. |
| Regresión del coach | Bridge degradable y tests del flujo YAML existente. |
| DB global accidental | Test que rechaza rutas fuera del proyecto. |
| Runtime omitido del bundle | Smoke de instalación inspecciona runtime y abre una sesión. |
