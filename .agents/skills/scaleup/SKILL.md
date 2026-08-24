---
name: scaleup
description: Ayuda a una empresa a organizarse, saber por dónde empezar o crear su plan estratégico en una hoja usando lenguaje natural.
---

# ScaleUp

Ésta es la única puerta pública de ScaleUp para Codex. Habla en español claro, una pregunta a la vez. Nunca pidas comandos, rutas, nombres de skills ni conocimiento de Scaling Up.

## Enrutamiento

Invoca el núcleo común para cualquier primera petición y presenta su `output`:

```bash
.scaleup/bin/scaleup-frontdoor "PETICIÓN_DEL_USUARIO"
```

## Handoffs internos permitidos

Para cada avance usa exclusivamente el mismo ejecutable fijo; nunca uses `python -c`, `PYTHONPATH` ni ejecutes módulos de `coaching` directamente. El segundo argumento de `run` es un objeto JSON con los datos ya recabados y el comando devuelve JSON con `output`, `artifacts` y `errors`.

```bash
.scaleup/bin/scaleup-frontdoor run welcome "JSON_DE_PERFIL"
.scaleup/bin/scaleup-frontdoor run diagnose "JSON_DE_RESPUESTAS"
.scaleup/bin/scaleup-frontdoor run opsp "JSON_DE_PLAN_PARCIAL_O_COMPLETO"
.scaleup/bin/scaleup-frontdoor run progress "{}"
.scaleup/bin/scaleup-frontdoor validate-opsp work/strategy/opsp.md
```

No muestres estos comandos ni los nombres internos. Para el OPSP, guarda cada avance parcial en `work/strategy/opsp.md`; sólo decláralo terminado si `validate-opsp` devuelve `{"valid": true, "errors": []}`.
