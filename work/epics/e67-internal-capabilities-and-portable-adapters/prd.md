---
epic_id: "E67"
title: "PRD — Capacidades internas y adaptadores portables"
status: "planned"
depends_on: ["E45", "E65", "E56"]
---

# PRD E67 — Capacidades internas y adaptadores portables

## Problema

La metodología y los procedimientos deben sobrevivir un cambio entre Codex y
Claude. Copiar instrucciones distintas para cada plataforma provoca divergencia
silenciosa; publicar cada procedimiento como comando convierte una experiencia
para empresarios no técnicos en un catálogo técnico.

## Resultado para el empresario

La instalación expone una sola puerta: **Escala**. Éste identifica la intención,
usa la capacidad interna pertinente y entrega el artefacto; la persona no
aprende nombres de skills, rutas de archivos ni subagentes.

## Arquitectura de producto

```text
procedimiento verificado
  → capability contract versionado
  → orquestador Escala
  → adaptador Codex o Claude
  → mismo artefacto, evidencia y límites
```

El núcleo declara `trigger`, `non_trigger`, entradas, salida, evidencia,
actualización de estado, límites y versión. Los adaptadores sólo traducen cómo
la plataforma instala instrucciones y, cuando corresponda, perfiles internos.
No contienen una segunda versión de la metodología.

## Reglas no negociables

1. Los cuatro perfiles E45 son definiciones privadas bajo demanda, no comandos
   públicos ni procesos persistentes.
2. Un alias de compatibilidad redirige al contrato canónico; no ejecuta lógica
   duplicada.
3. La misma intención debe producir artefactos semánticamente equivalentes en
   ambas plataformas, aunque el texto no sea idéntico.
4. Todo cambio de estado continúa local y consentido; ningún adaptador crea un
   backend central como requisito de instalación.
5. Si una plataforma no soporta una extensión, el adaptador la declara como
   límite en vez de inventar paridad.

## Entregables

- Catálogo `procedure → capability → lifecycle → evidence` validable.
- Adaptador Codex generado desde el core.
- Adaptador Claude generado desde el mismo core.
- Paquete privado de Cash, Execution, People y Strategy desde contratos E45.
- Matriz de paridad: intentos, ruta elegida, artefacto, evidencia, límites y
  diferencias observadas.
- Instalador que no sobrescribe memoria empresarial ni exige servicios remotos.

## Criterios de aceptación

- Una instalación limpia muestra sólo Escala como experiencia pública.
- Las seis rutas MVP y las cuatro decisiones se prueban en ambas plataformas.
- No existe lógica metodológica duplicada en aliases/adaptadores.
- Los perfiles privados no aparecen como elecciones del empresario.
- Un fallo de instalación informa el límite y preserva datos locales.
- E68 valida en entornos limpios antes de prometer distribución o paridad.

## Fuera de alcance

- Resolver diferencias de modelo mediante prompts ocultos.
- Distribuir subagentes como una “plantilla de empleados virtuales”.
- Reescribir ontología, evidencia E55 o procedimientos E65.
- Exigir a un empresario seleccionar Codex vs. Claude para completar un flujo.
