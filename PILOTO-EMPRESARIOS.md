# ESCALA — piloto privado para empresarios

ESCALA es un asesor local que te ayuda a ordenar tu negocio —tu equipo, tus
clientes y tu estrategia, tu día a día y tu dinero— a partir de la información
que tú decides compartir. Esta es una beta privada:
te ayuda a trabajar, aprender y dar feedback; no sustituye asesoría legal,
fiscal o financiera profesional ni se presenta como producto oficial de una
metodología externa.

## Antes de instalar

- Usa una computadora de trabajo que controles y una carpeta donde puedas
  guardar la información de tu empresa.
- Para el primer recorrido usa datos de ejemplo o información no sensible.
  ESCALA debe pedir tu confirmación antes de guardar o indexar material
  delicado.
- Necesitas Git, Python 3, `uv` y uno de estos agentes locales: Claude Code,
  Codex CLI o Hermes Agent.
- La ruta recomendada y observada en un entorno real es Claude Code.
  En Windows, usa WSL2 hasta que concluya la calificación nativa de Windows.

## Instalación (10 minutos)

Abre una terminal y ejecuta:

```bash
git clone https://github.com/lunitomx/agente-de-escalamiento.git
cd agente-de-escalamiento
./install.sh --platform claude
```

Para Codex o Hermes, sustituye `claude` por `codex` o `hermes`. Cada
instalación elige explícitamente una plataforma; no configura las demás.

Después abre tu agente en esa carpeta y escribe, con tus propias palabras:

> Quiero empezar. Te voy a contar de mi empresa y el reto más importante que
> tengo hoy.

## Tu primera sesión

1. Describe qué vendes, a quién y qué te preocupa hoy.
2. Confirma o corrige el resumen que ESCALA entendió.
3. No tienes que elegir un área: cuéntale a ESCALA lo que más te preocupa.
4. Pide que lo convierta en una decisión, una acción, un responsable y una
   fecha de revisión.
5. En la siguiente conversación, pídele revisar qué ocurrió y corrige cualquier
   aprendizaje antes de reutilizarlo.

No necesitas calificar a tu empresa del 1 al 5 ni aprender comandos internos.
ESCALA debe empezar por evidencia y preguntas abiertas, y usar una calificación
solo cuando haya contexto suficiente y te explique qué significa.

## Cómo protege tu información

- Tu información vive en la carpeta local que eliges.
- Puedes compartir documentos de trabajo con tu equipo mediante Drive u
  OneDrive, pero no debes sincronizar SQLite: cada instalación conserva su
  propia caché local.
- No cargues contraseñas, estados de cuenta completos, identificaciones,
  contratos confidenciales ni evaluaciones de personas sin revisar primero qué
  se guardará.
- Las automatizaciones son sugerencias: se explican y requieren tu aceptación.

## Qué feedback necesitamos

Al terminar una sesión, comparte sólo lo que te resulte cómodo:

- qué problema intentabas resolver;
- si entendiste la recomendación y el siguiente paso;
- qué evidencia o pregunta faltó;
- qué acción decidiste tomar; y
- qué debería ser más claro, más corto o más útil.

No envíes archivos sensibles por este feedback. Si decides participar en el
piloto de aprendizaje, se registra únicamente una referencia opaca y los
resultados del piloto permanecen en tu instalación local.

## Actualizar

Desde la carpeta del repositorio:

```bash
git pull --ff-only
./install.sh --platform claude
```

El instalador reutiliza el entorno local `.venv`; no usa `pip` global.
