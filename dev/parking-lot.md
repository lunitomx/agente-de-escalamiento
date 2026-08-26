# Parking Lot

> Ideas condicionadas, no compromisos ni épicas activas.

**Última revisión:** 2026-08-26

## From E10: Cross-Platform Distribution

| Item | Origin | Estado auditado | Priority | Promotion Condition |
|------|--------|------------------|----------|---------------------|
| Dashboard web para ScaleUp | E10 scope | Parcialmente cubierto por E14–E18: existen 22 dashboards y servidor local; no existe producto web alojado/multiusuario | Low | Cuando haya usuarios activos fuera de Eduardo y se necesite acceso remoto |
| API REST del coaching engine | E10 scope | Parcialmente cubierto por la API local de E18–E20; no existe un servicio público del coaching engine | Medium | Cuando se necesite integración con apps externas |
| Publicar skills como "tap" de Hermes | E10 scope | El bundle público/installer existe por E11; el formato específico de tap no está verificado | Low | Cuando el bundle esté estable, testeado y Hermes sea canal activo |
| ScaleUp en Claude Desktop (MCP server) | E10 scope | No iniciado | Medium | Cuando Claude Desktop soporte el flujo requerido y exista demanda |

## Investigación externa

| Item | Origin | Estado auditado | Priority | Promotion Condition |
|------|--------|------------------|----------|---------------------|
| Aprendizajes de LifeOS para ScaleUp | [LifeOS README](https://github.com/danielmiessler/LifeOS) (2026-08-26) | README auditado: propone un skill único autocontenido con memoria persistente, contexto, routing inteligente y mejora continua; su instalador conserva `USER/` y personalizaciones. LifeOS es personal y generalista: no copiar su infraestructura ni telemetría sin evaluación propia de producto, privacidad y seguridad. | Medium | Promover a una épica con el siguiente ID disponible sólo si una auditoría separa patrones reutilizables del dominio empresarial de ScaleUp, define valor medible y valida privacidad, instalación reversible y compatibilidad Claude/Codex. |
| Experiencia visual por host (ChatGPT Work / Claude Cowork) | Consulta de producto (2026-08-26) | Pendiente de auditoría comparativa. ChatGPT documenta flujos para visualizaciones, dashboards privados y apps internas con Sites, pero no se asumirá paridad con Claude Cowork ni que el agente pueda elegir una superficie visual sin conocer el host y sus permisos. | Medium | Promover sólo cuando se confirme con documentación oficial vigente qué admite cada host, haya detección honesta de capacidad y permisos, fallback portable en HTML/Markdown/archivos locales, reglas de privacidad y pruebas de punta a punta en ambos. |

## Reglas de promoción

- Un elemento del parking lot no recibe número de épica hasta tener objetivo,
  alcance, dependencias y criterio de éxito aprobados.
- El siguiente número disponible es E33.
- La deuda técnica ya comprometida se mantiene en
  work/epics/product-roadmap.md, no se duplica aquí.
