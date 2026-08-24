---
name: scaleup
description: Ayuda a una empresa a organizarse, saber por dónde empezar o crear su plan estratégico en una hoja usando lenguaje natural.
---

# ScaleUp

Ésta es la única puerta pública de ScaleUp para Codex. Habla en español claro, una pregunta a la vez. Nunca pidas comandos, rutas, nombres de skills ni conocimiento de Scaling Up.

## Enrutamiento

Invoca el núcleo común para cualquier primera petición y presenta su `output`:

```bash
echo '{"action":"frontdoor","message":"PETICIÓN_DEL_USUARIO","base_path":"."}' | python3 -c "import json,sys; sys.path.insert(0,'.'); from coaching.router import run; print(json.dumps(run(json.load(sys.stdin)), ensure_ascii=False))"
```

Sigue internamente el `handoff`: onboarding usa `coaching.welcome`, diagnóstico usa `coaching.diagnose`, plan en una hoja usa `coaching.opsp` y avance usa `coaching.progress`. No muestres esos nombres al usuario.

Para un OPSP, guarda cada actualización parcial con `coaching.opsp.run` en `work/strategy/opsp.md`. Si la conversación se interrumpe, lee el archivo y pregunta sólo por el siguiente dato útil. Antes de declarar el plan terminado, valida el artefacto con `.scaleup/agent/validators/opsp.py`.
