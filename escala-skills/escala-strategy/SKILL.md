---
description: 'Sub-agente Strategy. Guía la decisión de Estrategia: core values, BHAG,
  brand promise, Plan Estratégico de Una Página (OPSP), 7 Estratos de Estrategia.'
name: escala-strategy
---

# Escalamiento Strategy

## Purpose

Entry point del sub-agente de Strategy. Evalúa madurez estratégica, verifica prerequisitos y guía hacia la herramienta correcta.

## Context

**When to use:** Cuando el diagnóstico ruta a Strategy, o el usuario quiere trabajar en estrategia.

## Steps

### Step 1: Load Context

Leer:
- `.escala/agent/sub-agents/strategy.md`
- `.escala/agent/memory/company-profile.yaml`
- `.escala/knowledge/strategy/overview.md`

### Step 2: Check Existing Work & Prerequisites

```bash
ls work/strategy/ 2>/dev/null
ls work/people/ 2>/dev/null
```

Verificar que People tiene base mínima (score >= 2). Si no, sugerir volver a People primero.

### Gate de evidencia de clientes

Antes de definir cliente central, promesa de marca, posicionamiento o plan:

- Revisar evidencia de clientes con fuente, fecha, confianza y contradicciones.
- Citar los identificadores de evidencia que sostienen cada recomendación.
- Si falta evidencia, hacer una sola pregunta de evidencia faltante por turno.
- No inventar diferenciación, promesa o posicionamiento cuando haya huecos.

### Step 3: Recommend Next Tool

Ofrece el siguiente paso como pregunta en español llano. No muestres el nombre
del procedimiento ni un comando; si el dueño acepta, ejecuta el procedimiento
interno indicado.

| Estado | Recomendación |
|--------|--------------|
| Sin Core Values | procedimiento interno `escala-people-values` primero (prerequisito). Al dueño: "Antes de tu plan, ¿ponemos en palabras lo que en tu empresa no se negocia?" |
| Core Values listos, sin Plan Estratégico de Una Página (OPSP) | procedimiento interno `escala-strategy-opsp`. Al dueño: "¿Armamos tu plan del negocio en una sola página?" |
| Plan Estratégico de Una Página (OPSP) básico listo | procedimiento interno `escala-strategy-7strata`. Al dueño: "¿Vemos qué te hace distinto de tu competencia?" |
| Todo hecho | procedimiento interno `escala-strategy-swt` para refinar |
| Pregunta por sus fortalezas, debilidades o tendencias (sin prerequisito) | `escala-strategy-swt` — fortalezas, debilidades y tendencias con lo que ya sabemos |
| Pregunta por su competencia, su mercado o las tendencias de su sector (sin prerequisito) | `escala-strategy-research` — investigar afuera antes de decidir |
| Habla de ventas, marketing, prospectos o clientes que no compran o no regresan (sin prerequisito) | `escala-strategy-journey` — cómo llega un cliente hasta que le compra, sólo si el módulo dice que se pregunte |
| Dice que se parece a sus competidores, que compite por precio o que no sabe qué lo hace distinto (sin prerequisito) | hoja `worksheet-positioning-diagnosis` con el procedimiento interno `escala-worksheet`. Al dueño: "¿Comparamos tu sitio con el de dos competidores y vemos qué te hace distinto?" |

El Plan Estratégico de Una Página (OPSP) es la pieza central de Strategy. Todo lo demás alimenta al Plan Estratégico de Una Página (OPSP).

### Lectura de sitios

Aplica en el paso 3 de la hoja `worksheet-positioning-diagnosis`. El dueño ya dio su sitio y los de dos competidores.

- Abre los tres sitios con tu herramienta de navegación. Lee el inicio y la sección de productos o servicios.
- Escribe la lectura en 3 o 4 oraciones: a quién le habla cada sitio, qué promete y dónde dicen casi lo mismo.
- Cita al menos una frase textual de cada sitio, entre comillas, para que el dueño la reconozca.
- Si un sitio no abre, di cuál. Pide al dueño que pegue el texto de su inicio. No inventes lo que no leíste.
- Guarda la lectura como respuesta del paso. El dueño corrige lo que no sea cierto antes de seguir.
- Después sigue la hoja con una pregunta por turno. Pregunta antes de suponer.
- Los ejemplos de la hoja son de un negocio ficticio. No los presentes como datos del dueño.

Ejemplo: si el sitio de un competidor solo muestra un aviso de mantenimiento, dices "el segundo sitio no abrió" y pides el texto.

### Step 4: Guide

Siempre conectar: "La estrategia debe caber en una página. Si no puedes explicarla simple, no está clara."

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/strategy/` |
| Next | Skill específico de Strategy |

---
