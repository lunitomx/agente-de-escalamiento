# ADR-022: Memoria SQLite por proyecto y hechos confirmados

**Estado:** Aprobada para E22
**Fecha:** 2026-08-26

## Contexto

ScaleUp guarda hoy perfil, conversación y plan como YAML/Markdown del proyecto.
E18 implementó SQLite, hechos, grafo y sesiones, pero su CLI usa por defecto una
base global en el directorio personal y el instalador no lo distribuye. Eso puede
mezclar empresas y deja dos fuentes de verdad.

## Decisión

1. Cada proyecto tendrá una sola base en .scaleup/memory/escala.db.
2. SQLite será la fuente de verdad para la memoria empresarial; YAML y Markdown
   existentes se migran de manera idempotente y siguen como vistas/artefactos
   compatibles durante la transición.
3. La memoria sólo guarda hechos, decisiones y aprendizajes con fuente,
   categoría, fecha y confianza. Las inferencias del modelo se presentan como
   propuestas y nunca se persisten sin confirmación explícita.
4. El inicio de conversación recupera contexto desde esa base. El cierre se
   ejecuta por una interacción natural y confirma qué aprendizajes guardar.
5. La ausencia o corrupción de la base no bloquea el coach: se conserva el
   flujo YAML actual y se ofrece recuperación segura.

## Consecuencias

- El instalador debe distribuir el runtime SQLite, migrador y bridge, no sólo
  coaching.
- El bridge debe recibir explícitamente la raíz de proyecto; quedan prohibidos
  defaults globales para datos de empresa, PID, logs o sesiones.
- La migración y el rollback son parte del contrato de release.
- No se añade vector store, cloud o plugin externo en E22.

## Alternativas descartadas

| Alternativa | Motivo |
|---|---|
| Mantener YAML y SQLite como fuentes permanentes | Genera divergencia y respuestas inconsistentes. |
| Usar la base global de E18 | Mezcla empresas y no es portable por proyecto. |
| Persistir cada inferencia automáticamente | Convierte alucinaciones en memoria empresarial. |
| Añadir embeddings ahora | No resuelve la integración ni justifica complejidad adicional. |

## Verificación

- Una instalación limpia crea datos sólo bajo la carpeta del proyecto.
- Una segunda migración no duplica compañías, sesiones ni hechos.
- Una sesión nueva recupera hechos confirmados sin historial de chat.
- Un hecho rechazado no aparece en recuperación posterior.
