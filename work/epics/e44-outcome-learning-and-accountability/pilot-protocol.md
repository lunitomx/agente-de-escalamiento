---
epic_id: "E44-E45"
document_status: "ready-for-human-pilot"
epic_status: "in_progress"
---

# Protocolo de piloto empresarial E44/E45

## Propósito

Obtener la aceptación real que falta sin tratar una fixture como evidencia de
negocio y sin guardar nombres, conversaciones, archivos o cifras de la empresa
en este repositorio.

## Antes de iniciar

- Una persona dueña participante acepta el piloto y usa un identificador opaco,
  por ejemplo `owner-001`; la empresa usa otro, por ejemplo `company-001`.
- Todo dato real permanece en la instalación local de la empresa. Este repo
  conserva, como máximo, un recibo privado con estados booleanos y referencias
  opacas.
- Para el ciclo People, se confirma consentimiento explícito antes de registrar
  una lección o resultado relacionado con personas.

## Sesión E44 — cuatro ciclos

Para People, Strategy, Execution y Cash, la persona dueña revisa una decisión,
una acción y un resultado observado o `no_result_yet`. Después confirma,
corrige o rechaza la lección. La retrospectiva debe registrar si el cockpit
mostró el siguiente paso sin exponer IDs ni convertir correlación en causalidad.

## Sesión E45 — comparación honesta

Se evalúan los mismos datos locales en dos rutas: análisis de coach único y
equipo privado. No se fuerza que el equipo gane.

1. Caso Cash + Execution: comprobar periodo/unidad y pedir un dato si falta.
2. Caso Strategy + People + Execution: hacer visible la tensión y la pregunta
   que la resolvería.

En cada caso se usa como máximo una ronda de aclaración, una respuesta ejecutiva
única y el contexto mínimo. La dueña marca valor `higher`, `equal`, `lower` o
`inconclusive`; si no es mayor, la conclusión requerida es reducir el equipo o
pedir más evidencia.

## Recibo y gate

Crear un recibo privado que cumpla
`validators/e44_e45_business_pilot.py` y validarlo con:

```text
uv run python scripts/check_e44_e45_business_pilot.py <recibo-privado.json>
```

El recibo sólo puede declarar `pass` si contiene los cuatro ciclos, ambos casos
comparativos, aceptación de la dueña, retrospectiva, consentimiento People y
almacenamiento `private-local-only`. El validador no recoge respuestas ni datos
del negocio.

## Decisión de cierre

- E44 cierra sólo con una retrospectiva y aceptación reales.
- E45 cierra sólo si la comparación produce una decisión explícita de retener,
  reducir o seguir midiendo el equipo; E67 sigue siendo necesario para instalar
  los contratos en plataformas.
