---
epic_id: "E55"
title: "Onboarding multifuente y conciliación de métricas de negocio"
status: "complete"
created: "2026-08-21"
jira_key: "ESCALA-20"
source_issue: "https://github.com/lunitomx/agente-de-escalamiento/issues/9"
---

# E55 — Onboarding multifuente y conciliación de métricas de negocio

## Hipótesis

Antes de diagnosticar o recomendar, ESCALA debe construir una evidencia trazable de la empresa: distinguir métricas que parecen iguales pero no lo son, reutilizar lo que ya se sabe y dejar claro qué falta. Un onboarding que acepta múltiples fuentes (conversación, hojas de cálculo, catálogos, exportaciones de plataformas) y las concilia de forma conservadora reduce el riesgo de recomendar sobre datos mal comparados.

## Métricas de éxito

- Un hecho persistido conserva fuente, periodo, definición, base temporal, confianza y estado de comparabilidad.
- El dashboard de evidencia puede mostrarse antes de tener scores completos y deja claro qué se sabe, qué falta y qué no es comparable.
- El onboarding reutiliza hechos ya autorizados, hace una pregunta a la vez y ramifica solo hacia vacíos reales.
- El flujo de conciliación impide comparar métricas de naturaleza distinta sin advertencia explícita.
- El board recibe un paquete de evidencia y declara límites cuando aún faltan datos.

## Tamaño

L — seis historias de producto más calificación.

## No-Gos

- No enviar datos de la empresa fuera del directorio local.
- No inferir scores de People, Strategy, Execution o Cash antes de tener evidencia suficiente.
- No fusionar entidades (clientes, transacciones) de forma agresiva; la ambigüedad debe quedar explícita.
- No construir conectores OAuth o APIs de terceros; solo se aceptan archivos exportados localmente.
- No duplicar la lógica de marketing de Kokoro; Escala consume eventos canónicos, no los produce.

## Rabbit Holes

- Diseñar un modelo ontológico universal de métricas de negocio en lugar de un contrato acotado.
- Intentar normalizar automáticamente formatos de archivo propietarios.
- Resolver ambigüedades de identidad con heurísticas agresivas.
- Mezclar este trabajo con la consolidación del catálogo de skills (E56); son épicas separadas.
