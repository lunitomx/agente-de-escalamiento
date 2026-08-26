# Epic Brief: E22 — Memoria Empresarial Integrada

## Visión

Convertir la persistencia fragmentada de ScaleUp en una memoria empresarial
local-first: una fuente de verdad por empresa que conserve hechos, decisiones,
aprendizajes, relaciones, cambios y contexto relevante entre sesiones.

## Por qué es una épica separada

E18 ya construyó SQLite, memoria de hechos, grafo y ciclo de sesión; E10 y el
front door actual distribuyen y usan otro runtime, basado en YAML. La auditoría
RaiSE de 2026-08-26 confirmó que ningún artefacto de E18 se instala ni se invoca
desde una instalación pública. Esta épica cierra esa brecha sin sumar un plugin
externo ni crear dos fuentes de verdad.

## Promesa de producto

- Al abrir una nueva sesión, ScaleUp recupera sólo el contexto relevante y los
  cambios desde la última conversación.
- Al cerrar o pausar una sesión, conserva decisiones y aprendizajes confirmados
  por la persona, con fuente, fecha, categoría y confianza.
- Personas, métricas, prioridades y decisiones pueden relacionarse y consultarse
  sin depender de la memoria efímera del modelo.
- Todo vive localmente bajo control de la empresa y sobrevive a Claude, Codex o
  Hermes.

## Hipótesis

Si ScaleUp instala una memoria SQLite única y la integra de manera explícita al
ciclo natural de conversación, una persona puede retomar su empresa con contexto
útil y verificable sin volver a explicar decisiones pasadas ni aceptar que el
modelo invente aprendizajes.

## Métricas de éxito

1. Una instalación limpia en Claude Code, Codex y Hermes contiene el runtime de
   memoria y crea una base local por proyecto, no una base global compartida.
2. La migración YAML → SQLite es idempotente y no pierde el perfil, diagnóstico,
   plan ni hojas existentes.
3. Una sesión nueva recupera hechos relevantes, cambios y siguiente paso desde
   SQLite; no depende del historial de chat.
4. Los hechos/decisiones guardados tienen fuente y sólo se persisten tras una
   regla de confirmación explícita y testeada.
5. El smoke E2E instalar → conversar → cerrar → sesión nueva → recuperar pasa
   en los clientes soportados.

## Appetite

L (6–10 historias). Es integración transversal de almacenamiento, contrato de
datos, migración, instalador y experiencia de usuario. No se implementará por
parches aislados al YAML o copiando un directorio sin pruebas de ciclo completo.

## Rabbit holes a evitar
