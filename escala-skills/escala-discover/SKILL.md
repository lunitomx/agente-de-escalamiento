---
description: 'Detecta dónde están los datos del negocio y sugiere el skill correcto de E30 para leerlos. "¿Tus datos están en Excel, PDF, CRM, Google Drive o en tu cabeza?"'
name: escala-discover
---

# Escalamiento — Discovery de Fuentes de Datos

## Purpose

El empresario ya tiene sus datos en algún lado. No necesita re-escribirlos en worksheets. Este skill detecta dónde están sus datos (Excel, Google Drive, CRM, PDF, cabeza) y lo conecta con el skill de E30 correcto para leerlos automáticamente.

## Steps

### Step 1: Preguntar — ¿dónde están tus datos?

"Para trabajar en [tema], necesito algunos datos. Pero no te preocupes — no vas a llenar planillas. ¿Dónde tienes esta información hoy?"

Escuchar la respuesta y clasificar:

### Step 2: Clasificar fuente y sugerir skill

| El usuario dice... | Fuente detectada | Skill sugerido |
|---|---|---|
| "Tengo un Excel / Google Sheets" | Spreadsheet | "Compártelo. Yo leo las celdas y extraigo lo que necesito." → E30.1 |
| "Mi contador me manda PDFs" | PDF | "Súbelo. Extraigo los números clave." → E30.2 |
| "Tengo un CRM (HubSpot, Salesforce...)" | CRM | "¿Puedes exportar un CSV? Es un botón en todos los CRMs." → E30.3 |
| "Usamos Google Drive para todo" | Drive | "Si estás en Claude Code, conéctame a tu Drive. Si no, comparte el archivo." → E30.1/E30.2 |
| "Tomamos foto del pizarrón en el daily" | Foto | "Perfecto. Súbela y yo extraigo los WWWs." → E30.4 |
| "Está en mi cabeza" | Memoria | "Perfecto. Eso también funciona. Dime los 5-6 números clave." → guiar manualmente |
| "No tengo nada documentado" | Sin datos | "No hay problema. Muchos empiezan así. Vamos a crear la estructura juntos." → worksheet del tema |

### Step 3: Verificar formato

Una vez identificada la fuente, verificar que el formato sea legible:

**Spreadsheet:**
- ¿Tiene encabezados? → Si no, preguntar qué significa cada columna.
- ¿Está en la primera hoja? → Si no, preguntar cuál.

**PDF:**
- ¿Es un PDF de texto o escaneado? → Si es escaneado, advertir que la extracción puede ser menos precisa.
- "¿Estos son los estados financieros del último trimestre?"

**CRM CSV:**
- Detectar columnas automáticamente: name, value, stage, date, owner.
- Si alguna columna es ambigua, preguntar: "Esta columna 'Status' ¿es la etapa del deal?"

### Step 4: Ejecutar la lectura

Invocar el skill de E30 correspondiente con el archivo proporcionado.

"Perfecto. Dame un segundo — estoy leyendo tu [tipo de archivo]..."

Ejecutar el skill de lectura. Mostrar resultados extraídos.

"Esto es lo que extraje. ¿Es correcto?"

Si hay errores, ajustar. Si está correcto, continuar.

### Step 5: Conectar con el flujo

Una vez que los datos están leídos y validados, continuar con el skill que los necesita.

"Ya tengo tus datos. Ahora [continuar con el flujo original]."

## Notas

- Si el usuario tiene datos en múltiples fuentes, priorizar: leer UNA fuente primero, validar, luego la siguiente.
- Si el usuario no quiere compartir ciertos datos, respetar: "OK, trabajemos con lo que tienes. Podemos estimar el resto."
- La detección de formato es automática — si no se puede, preguntar.
- Este skill es un puente: detecta → sugiere → ejecuta. No reemplaza los skills de E30, los activa.
