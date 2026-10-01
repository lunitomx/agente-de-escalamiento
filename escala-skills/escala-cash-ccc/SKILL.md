---
description: >-
  Mapea el Ciclo de Conversión de Efectivo (CCC) con DSO/DIO/DPO (365 días).
  Basado en Alan Miltz. Identifica qué aprieta el cash flow.
name: escala-cash-ccc
---

# Escalamiento Cash — CCC (Ciclo de Efectivo)

## Purpose

Mapear el CCC: días que tarda tu dinero en regresar como cash. Identificar
si el problema es cobro, inventario o pagos.

## ⚠️ Reglas

Base **365 días**, NO 30. Idioma humano (tooltips). Fórmulas:

```
DSO = Cuentas x Cobrar / (Ventas Anuales / 365)
DIO = Inventario / (COGS Anual / 365)
DPO = Cuentas x Pagar / (COGS Anual / 365)
CCC = DSO + DIO - DPO
```

| CCC | Significa |
|-----|-----------|
| > 60d | Peligro. Cobranza urgente |
| 30-60d | Regular. Revisar componente más largo |
| < 30d | Sano |
| Negativo | Proveedores te financian (común en SaaS) |

## Steps

1. Preguntar datos en humano: ventas, costo, cuentas x cobrar, inventario, cuentas x pagar
2. Calcular DSO/DIO/DPO/CCC
3. Identificar cuál de los 3 aprieta más
4. Recomendar acción priorizada
5. Guardar en `work/cash/ccc-analysis.md`

---

*Metodología: Alan Miltz. Implementación: Humberto Martínez Barrón. Adaptación: Kokoro.*
