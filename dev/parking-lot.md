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
| Aprendizajes de LifeOS para ScaleUp | [LifeOS README](https://github.com/danielmiessler/LifeOS) (2026-08-26) | README auditado: propone un skill único autocontenido con memoria persistente, contexto, routing inteligente y mejora continua; su instalador conserva `USER/` y personalizaciones. LifeOS es personal y generalista: no copiar su infraestructura ni telemetría sin evaluación propia de producto, privacidad y seguridad. | Medium | Promover a E23 sólo si una auditoría separa patrones reutilizables del dominio empresarial de ScaleUp, define valor medible y valida privacidad, instalación reversible y compatibilidad Claude/Codex. |

## Reglas de promoción

- Un elemento del parking lot no recibe número de épica hasta tener objetivo,
  alcance, dependencias y criterio de éxito aprobados.
- El siguiente número disponible es E23.
- La deuda técnica ya comprometida se mantiene en
  work/epics/product-roadmap.md, no se duplica aquí.
