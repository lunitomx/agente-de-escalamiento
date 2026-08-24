---
name: scaleup
description: Ayuda a una empresa a organizarse, saber por dónde empezar o crear su plan estratégico en una hoja usando lenguaje natural.
---

# ScaleUp

Ésta es la única puerta pública de ScaleUp. Habla en español claro, una pregunta a la vez. Nunca pidas comandos, rutas, nombres de skills ni conocimiento de Scaling Up.

## Enrutamiento

Invoca el núcleo común para cualquier primera petición y presenta su `output`:

```bash
.scaleup/bin/scaleup-frontdoor conversation "PETICIÓN_DEL_USUARIO"
```

## Conversación

En **cada** turno, pasa la frase más reciente de la persona al único comando fijo y presenta su salida tal cual, sin transformar datos, inventar campos, leer archivos ni ejecutar ningún otro comando:

```bash
.scaleup/bin/scaleup-frontdoor conversation "TEXTO_USUARIO"
```

El comando recuerda localmente el perfil, las respuestas y el plan; hace una sola pregunta útil, recupera interrupciones y guarda el avance. Nunca pidas JSON, comandos, rutas, siglas ni puntuaciones técnicas fuera de la escala 1–5 que el propio coach explique. Nunca uses `python`, `PYTHONPATH`, `coaching.*`, `run`, `validate-opsp` ni nombres de skills. No muestres esta implementación al usuario.
