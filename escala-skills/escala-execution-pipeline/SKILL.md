---
description: 'Exporta tu pipeline de ventas a CSV desde cualquier CRM y te digo qué está pasando: deals estancados, velocidad, y si tu pipeline alcanza para la meta.'
name: escala-execution-pipeline
---

# Escalamiento Execution — De tu Pipeline al Scorecard de Ventas

## Purpose

No sé qué CRM usas, y no necesito saberlo. Solo necesito que exportes tu pipeline a un CSV — todos los CRMs lo hacen. Yo lo leo, analizo, y te digo si tu pipeline está sano o si hay deals pudriéndose que nadie está viendo.

## Steps

### Step 1: Recibir el pipeline

"¿Qué CRM usas? No importa cuál. Solo necesito que exportes tu pipeline a CSV."

Instrucciones para los CRM más comunes:
- **HubSpot:** Reports → Create Report → Export to CSV
- **Salesforce:** Reports → Export → CSV
- **Pipedrive:** Deals → Export → CSV
- **Kommo:** Leads → Export → CSV
- **Google Sheets:** Ya está listo, compártelo
- **Excel:** Súbelo

"Súbeme el CSV. Yo identifico las columnas automáticamente."

### Step 2: Analizar el pipeline

Del CSV extraer y calcular:

**Salud general:**
- Total de deals activos
- Valor total del pipeline
- Valor promedio por deal
- Tasa de ganancia histórica (si hay deals cerrados)

**Velocidad:**
- Deals por etapa
- Días promedio en cada etapa
- Deals estancados (más de 30 días en misma etapa)
- Velocidad de avance (cuántos deals avanzaron esta semana)

**Cobertura:**
- Pipeline coverage = Valor pipeline / Meta del trimestre
- "Necesitas 3-4x tu meta en pipeline para tener seguridad."
- Si coverage < 2x: ALERTA

### Step 3: Presentar diagnóstico

Mostrar dashboard en texto:

```
📊 Pipeline — Salud General
  Deals activos:     47
  Valor pipeline:     $1,250,000
  Deal promedio:      $26,595
  Tasa de ganancia:   28%

⏱️ Velocidad
  Deals en propuesta: 18 (38%)
  Estancados +30 días: 7 deals por $215,000 ⚠️
  Días promedio hasta cierre: 45

🎯 Cobertura vs Meta Q3 ($400K)
  Coverage: 3.1x ✅ Saludable
```

### Step 4: Alertas automáticas

- "7 deals están estancados más de 30 días. Son $215,000. ¿Quieres que los revisemos uno por uno?"
- "Tu tasa de ganancia es 28%. Si aplicas Topgrading a tu equipo de ventas, ¿podría subir a 35%?"
- "El 60% de tu pipeline está en 2 deals grandes. Si uno se cae, pierdes cobertura."
- "Tu velocidad de avance bajó este mes vs el mes pasado. ¿Cambió algo en el proceso?"

### Step 5: Guardar y próximos pasos

Guardar análisis en `work/execution/pipeline-scorecard.md`.

Preguntar: "¿Quieres que enfoquemos tu Prioridad #1 en ventas este trimestre?"

## Output

- Análisis completo del pipeline
- Deals estancados identificados
- Cobertura vs meta calculada
- Recomendaciones accionables con deals específicos

## Notas

- Este skill NO necesita conexión a CRM. El usuario exporta un CSV — todos los CRMs lo permiten.
- Si el usuario no tiene CRM, puede darte los datos de cabeza: "Tengo 5 deals: Cliente A por $50K en propuesta, Cliente B por $30K en negociación..."
- Las columnas del CSV se detectan automáticamente (name, value, stage, date, etc.)
