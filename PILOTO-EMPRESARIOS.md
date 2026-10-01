# ESCALA — piloto privado para empresarios

ESCALA es un asesor local que te ayuda a ordenar tu negocio —tu equipo, tus
clientes y tu estrategia, tu día a día y tu dinero— a partir de la información
que tú decides compartir. Esta es una beta privada:
te ayuda a trabajar, aprender y dar feedback; no sustituye asesoría legal,
fiscal o financiera profesional ni se presenta como producto oficial de una
metodología externa.

## Antes de instalar

- Usa una computadora de trabajo que controles: una Mac (o Linux). En Windows,
  por ahora necesitas WSL2; pide ayuda a quien te invitó.
- Ten a la mano tu cuenta de Claude (de pago, por ejemplo Pro). Con ella entras
  a Claude Code, el programa donde vive ESCALA.
- Para el primer recorrido usa datos de ejemplo o información no sensible.
  ESCALA debe pedir tu confirmación antes de guardar o indexar material
  delicado.
- No tienes que instalar nada más antes: el instalador prepara lo que falte.

## Instalación (3 pasos, unos minutos)

1. Abre la app Terminal. En Mac: presiona Cmd + Espacio, escribe "Terminal" y
   presiona Enter.
2. Copia esta línea, pégala en la Terminal, presiona Enter y espera a que diga
   "Listo":

   ```
   curl -fsSL https://raw.githubusercontent.com/lunitomx/agente-de-escalamiento/main/instalar.sh | sh
   ```

3. Pega la línea que te muestra al final, `cd ~/ESCALA && claude`, y presiona
   Enter. Si te pide entrar con tu cuenta de Claude o confiar en la carpeta
   ESCALA, acepta. Luego escribe con tus propias palabras, por ejemplo:

   > Quiero empezar. Te voy a contar de mi empresa y el reto más importante que
   > tengo hoy.

Si algo falla, el mensaje te dice qué hacer; casi siempre basta con volver a
pegar la misma línea. No se borra nada.

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

- Tu información vive en tu computadora, dentro de la carpeta ESCALA.
  Actualizar ESCALA no la toca.
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

Pega otra vez la línea del paso 2. Trae la versión nueva de ESCALA y no toca tu
información.

## Para quien te ayuda con la computadora

- `instalar.sh` prepara `uv` y su Python, Claude Code (con sus instaladores
  oficiales) y la copia de ESCALA en `~/ESCALA`; luego corre
  `./install.sh --platform claude --with-specialists`. Volver a correrlo hace
  `git pull --ff-only`: nunca borra ni descarta cambios.
- El detalle técnico de cada corrida queda en
  `~/.config/agente-de-escalamiento/instalacion.log`.
- La información de la empresa queda en `~/ESCALA/.escala/my-company/` y
  `~/ESCALA/.escala/agent/memory/`, fuera de lo que trae Git.
- Para Codex o Hermes, desde `~/ESCALA`: `./install.sh --platform codex` o
  `./install.sh --platform hermes`.
