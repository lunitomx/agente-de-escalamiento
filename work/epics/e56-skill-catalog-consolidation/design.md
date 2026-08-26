# Diseño E56 — Orquestación simple, capacidades con contrato

## Arquitectura objetivo

```text
Empresario (lenguaje natural)
          |
          v
  escala — orquestador público único
   |  carga estado, consentimiento y evidencia
   |  entiende intención / declara falta de datos
   v
Registro canónico de capacidades
   |  public | internal | deprecated | retired
   v
Módulo con contrato o skill canónico
   |  conserva procedencia y resultado
   v
Workspace local de la empresa
```

El orquestador no es un prompt gigantesco ni un catálogo escondido. Es un
contrato que: carga el contexto permitido, clasifica la intención, consulta el
registro, llama una capacidad con entrada explícita, devuelve un resultado en
lenguaje empresarial y registra límites/evidencia. Cuando no hay suficiente
contexto, pregunta o propone el siguiente paso; no elige una metodología al azar.

## Registro canónico

Se introducirá un archivo legible por humanos y máquinas. Cada entrada tendrá,
como mínimo:

```yaml
id: cash.weekly-review
title: Revisión semanal de caja
visibility: internal        # public | internal | deprecated | retired
entrypoint: escala-cash
implementation: escala_server.financial.weekly_review
aliases: [scaleup-cash]
consumer: orchestrator
requires: [consent, cash_evidence]
returns: [summary, evidence_refs, next_actions, limitations]
owner: financial
bitter_pill: keep           # keep | internalize | merge | retire
decision_receipt: E56/S56.1
```

El formato final se decidirá en S56.1 según las convenciones vigentes, pero sus
campos obligatorios y las validaciones anteriores no son opcionales. Un nombre
de directorio no será la fuente de verdad del producto.

## Política de ciclo de vida

| Estado | Puede invocarlo el empresario | Regla |
|---|---:|---|
| `public` | Sí, mediante `escala` | Tiene caso de aceptación y explicación empresarial. |
| `internal` | No directamente | El orquestador lo usa cuando su precondición se cumple. |
| `deprecated` | Sólo alias temporal | Redirige al canónico, informa la migración y tiene fecha/condición de retiro. |
| `retired` | No | Conserva recibo y regresión de reemplazo; no deja referencias rotas. |

## Migración por fases

1. **Inventariar y congelar la línea base.** Capturar hash, intención y pruebas
   de todas las fuentes antes de tocar rutas.
2. **Introducir el registro y la puerta única.** Agregar `escala` sin quitar
   los caminos actuales; validar casos naturales y especializados.
3. **Derivar distribución.** Los instaladores construyen/instalan sólo desde la
   fuente declarada; validar que Claude, Codex y Hermes no diverjan.
4. **Redirigir legados.** `scaleup-*` deja de ser implementación y se convierte
   en adaptador temporal o mensaje de migración, incluido Rockefeller tras su
   decisión explícita.
5. **Retirar y comprobar.** Sólo las entradas con reemplazo y pruebas pueden
   salir de distribución. El reporte final enumera lo conservado, internalizado
   y retirado.

## Propiedad y fronteras

| Componente | Dueño en E56 | No cambia |
|---|---|---|
| Registro, aliases, empaquetado y pruebas de deriva | E56 | Semántica de Cash/People/Strategy/Execution. |
| Hechos, evidencia y conciliación | E55 / E49 | Contrato de entrada del orquestador, salvo adaptación mínima. |
| Memoria y consentimiento persistente | E52 | No se almacena contenido nuevo sólo para catalogar skills. |
| Workspace e instalador local | E41 / E56 integración | Autoridad local y límites de privacidad. |

## Verificación

La implementación añadirá pruebas deterministas para: integridad del registro,
alias sin doble implementación, artefactos de instalación, rutas naturales y
golden cases de las familias de mayor valor. Las evaluaciones de modelo, si se
usan, complementan estas pruebas; no sustituyen contratos ni recibos.
