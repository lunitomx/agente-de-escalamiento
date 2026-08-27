---
epic_id: E74
title: Workspace compartido por empresa y colaboración multiempresa local
status: planned
depends_on: [E37, E52, E55, E67]
---

# PRD E74 — Workspace compartido por empresa y colaboración multiempresa local

## Problema

El dueño no trabajará solo: contador, director, ventas y otros colaboradores
necesitan ver la misma realidad de una empresa, mientras que un grupo puede
operar varias empresas. La arquitectura previa protege SQLite local, pero no
resuelve una autoridad compartible, control de conflictos ni aislamiento entre
empresas.

## Usuario y trabajo por resolver

Un equipo quiere que sus agentes locales lean y aporten a una misma carpeta de
empresa, compartida por su mecanismo de archivos elegido. Quiere visibilidad de
hechos, decisiones y artefactos sin convertir ESCALA en SaaS ni sincronizar una
base SQLite.

## Resultado de producto

Cada empresa tiene un workspace portable con archivos Markdown/YAML
estructurados como fuente compartible de colaboración. Cada instalación conserva
su configuración, credenciales y SQLite como cache/index local regenerable. Un
cambio relevante usa revisiones, owner y detección de conflicto; nada se fusiona
silenciosamente.

## Principios

1. Una empresa es un límite duro: nunca se consulta o mezcla estado de otra.
2. Markdown/YAML versionados son compartibles; SQLite nunca viaja por Drive ni
   es la única autoridad.
3. Ver no equivale a poder editar: owner/rol/política de cada artefacto define
   quién puede proponer, aprobar o resolver un conflicto.
4. Carpetas sincronizadas son transporte de archivos, no un servicio que
   ESCALA controle mediante API/OAuth.
5. El sistema usa “propuesta → revisión → aprobación” para hechos/decisiones
   sensibles, no last-write-wins silencioso.

## Historias

| ID | Historia | Resultado |
|---|---|---|
| S74.1 | ADR de autoridad compartida | Decide topology, estado portable, cache SQLite y compatibilidad con E37. |
| S74.2 | Registro de empresas | Crear/abrir/archivar empresa con ID, workspace y aislamiento verificables. |
| S74.3 | Esquema portable de estado | Perfil, hechos, decisiones, artefactos e historial tienen archivos versionados y validables. |
| S74.4 | Colaboración y conflictos | Propuestas, owners, revisiones, locks lógicos y reconciliación explícita. |
| S74.5 | Cache local y sync | SQLite local se regenera y detecta revisiones; nunca se comparte. |
| S74.6 | Calificación multiempresa | Dos empresas, tres colaboradores, conflicto y offline/reconexión pasan pruebas. |

## Métricas de éxito

- Un colaborador ve estado aprobado de su empresa sin copiarlo manualmente.
- Ningún conflicto relevante queda resuelto automáticamente por orden de sync.
- Una instalación puede reconstruir su cache desde archivos de empresa válidos.
- Cero fugas de datos entre empresas o SQLite dentro de carpeta compartida.

## Fuera

- Servicio hospedado, login central, Drive API/OAuth o colaboración en tiempo
  real tipo Google Docs.
- Sincronizar bases SQLite, secretos, conversaciones crudas o archivos
  financieros sin consentimiento.
- Resolver disputas empresariales: el sistema registra y presenta el conflicto.
