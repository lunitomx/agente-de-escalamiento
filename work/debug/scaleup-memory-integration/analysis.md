# RaiSE Debug — Integración de memoria de ScaleUp

**Fecha:** 2026-08-26
**Tier:** M — Ishikawa (varias causas posibles)
**Alcance:** por qué una instalación pública de ScaleUp no entrega la memoria
neurosimbólica/SQLite construida en `escala_server`.

## 1. Gemba: problema reproducido

| Campo | Evidencia |
|---|---|
| **Qué** | `install.sh --target codex` instala el coach YAML, no `escala_server`. |
| **Cuándo** | En una instalación limpia y en cualquier conversación pública. |
| **Dónde** | `.scaleup/install.sh` y `.scaleup/bin/scaleup-frontdoor`. |
| **Esperado** | Runtime local con SQLite, hechos, grafo y ciclo de inicio/cierre. |
| **Observado** | Runtime con `agent/`, `coaching/`, `knowledge/`, `bin/` y `my-company/`; cero bases `.db`, sin `escala-inicia` ni `escala-cierra`. Tras onboarding se crean sólo `.scaleup/agent/memory/company-profile.yaml` y `conversation.yaml`. |

## 2. Ishikawa

| Hipótesis | Prueba | Resultado | Conclusión |
|---|---|---|---|
| Falta un plugin externo (p. ej. Holographic) | Búsqueda de dependencias y referencias | No existe referencia a Holographic, embeddings o vector store. | Eliminada: no es una dependencia omitida. |
| El servidor no existe o no funciona | Inspección de `escala_server/` y E18 | Existen SQLite, `MemoryEngine`, `GraphEngine`, sesiones y pruebas. | Eliminada: los componentes existen. |
| El instalador los distribuye de forma implícita | Instalación aislada y lectura de `install.sh` | No copia `escala_server`, CLI de servidor ni migración; Git registra 0 commits que introduzcan `escala_server`/`MemoryEngine` en el instalador. | Confirmada: no hay distribución. |
| El front door los consume aunque no se copien | Lectura de `scaleup-frontdoor` y `conversation.py` | Sólo llama a `coaching.router.conversation`; no importa ni invoca `escala_server`, inicio/cierre o base SQLite. | Confirmada: no hay integración en tiempo de ejecución. |
| Fue una limitación técnica de dependencias | E18 seleccionó `sqlite3` y `http.server` nativos; sin dependencia externa obligatoria. | No explica la ausencia. | Eliminada como causa primaria. |

## 3. Causa raíz

E18 construyó el servidor de memoria como una línea de componentes separada, pero
no se creó un contrato de integración ni una prueba de aceptación de producto
`instalar → iniciar sesión → recuperar hechos → cerrar → persistir/aprender`.
El instalador previo (E10) siguió distribuyendo el runtime YAML de `coaching`.
El front door de la RC se simplificó para la demo y quedó conectado exclusivamente
a ese runtime. La retrospectiva de E18 marcó lifecycle completo, pero el roadmap
auditado ya reconoce la integración del servidor con el instalador como deuda P2.

La raíz sistémica no es un archivo que falte copiar: es la ausencia de una única
fuente de verdad y de un gate E2E que uniera E18 con la distribución pública.

## 4. Impacto

- La RC actual reanuda respuestas y plan, pero no aprende patrones ni conserva
  hechos relacionales confirmados entre sesiones.
- `escala_server` puede coexistir con YAML, pero conectarlo sin migración crearía
  dos fuentes de verdad.
- El término “memoria neurosimbólica” sólo es apropiado para la arquitectura
  prevista de E18; la implementación actual de memoria del producto es YAML.

## 5. Contramedida propuesta (no aplicada)

Promover una nueva épica de integración con una sola fuente de verdad local:

1. Instalar `escala_server` y su CLI en cada runtime sin servidor externo.
2. Migrar YAML existente a una base SQLite por proyecto de forma idempotente.
3. Conectar el front door a `escala-inicia` y `escala-cierra` para recuperar y
   persistir hechos, decisiones, cambios y aprendizajes confirmados.
4. Definir una política explícita de extracción, conflicto, confianza/decay y
   privacidad antes de guardar inferencias del modelo.
5. Añadir el smoke E2E de producto anterior como gate obligatorio de release.

## 6. Prevención

Todo componente marcado "instalable" debe tener una prueba de runtime que
verifique su presencia y uso desde una instalación limpia; componentes probados
aisladamente no pueden cerrar una promesa de distribución.
