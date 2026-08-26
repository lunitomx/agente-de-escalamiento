# ScaleUp Agent

ScaleUp es un coach para ordenar y escalar una empresa. Convierte conversaciones
sencillas en un diagnóstico, prioridades y un **plan estratégico en una hoja**.
No necesitas conocer Scaling Up, usar comandos ni saber programar.

## Empieza aquí

### 1. Descarga e instala

```bash
git clone https://github.com/lunitomx/scaleupagent.git
cd scaleupagent
bash .scaleup/install.sh --target claude
```

Para instalarlo para Codex, cambia el último comando por:

```bash
bash .scaleup/install.sh --target codex
```

Puedes comprobar qué quedó instalado con:

```bash
bash .scaleup/install.sh --target claude --status
bash .scaleup/install.sh --target codex --status
```

La instalación se puede ejecutar otra vez para actualizar ScaleUp y conserva el
trabajo de tu empresa. Para quitar ScaleUp de todos los canales instalados y
conservar ese trabajo, usa:

```bash
bash .scaleup/install.sh --uninstall
```

Para quitarlo de un solo canal, añade `--target claude` o `--target codex`.
`--purge` elimina el runtime instalado, incluido su directorio `my-company`,
pero **no** localiza ni borra artefactos creados en otras carpetas de proyecto.
Si deseas eliminar los datos de una demo, entra primero en la carpeta exacta de
esa demo, revisa `.scaleup/` y `work/strategy/opsp.md`, y elimínalos
manualmente. No hagas una limpieza amplia desde tu directorio personal ni desde
una carpeta que contenga otros proyectos.

### 2. Abre tu asistente y habla normalmente

Abre Claude Code o Codex dentro de la carpeta donde quieres trabajar con tu
empresa. Después escribe una de estas frases, tal cual o con tus propias
palabras:

> Quiero organizar mi empresa.

> No sé por dónde empezar para escalar mi negocio.

> Quiero hacer mi plan estratégico en una hoja.

ScaleUp debe hacer una pregunta a la vez, guardar el contexto y sugerir el
siguiente paso. No tienes que escribir nombres de herramientas, rutas de
archivos ni siglas.

## Qué obtienes

El recorrido de ScaleUp te ayuda a crear y conservar:

- Un perfil básico de tu empresa.
- Un diagnóstico de Personas, Estrategia, Ejecución y Efectivo.
- Prioridades y acciones de seguimiento.
- Un One Page Strategic Plan (OPSP): tu plan estratégico en una hoja.

Los datos de trabajo se guardan localmente en el directorio `.scaleup/` del
proyecto. La continuidad opcional sólo recuerda una declaración que confirmes
explícitamente con “sí”; una respuesta ambigua o “no” no la da por cierta. La
memoria y sus copias de seguridad viven en ese mismo proyecto, nunca en la
instalación compartida. Compártelos sólo si deseas que alguien más vea la
información de tu empresa.

Para una demostración, puedes decir “quiero pausar”, dar una decisión concreta y
responder “sí” cuando te pregunte si quieres recordarla. En una sesión nueva,
“retomemos” recupera únicamente esa decisión confirmada. No dictes contraseñas,
tokens, rutas ni comandos: ScaleUp los rechaza para esta continuidad local.

## Guía de demostración

Para un recorrido completo con empresa de ejemplo, usa
[el guion de demo](docs/demo-script.md). También puedes consultar
[el estado de preparación](docs/demo-readiness.md), que distingue lo validado
de lo que aún está en construcción.

## Requisitos

- Claude Code o Codex instalado y con acceso a un modelo.
- Git y Bash para descargar e instalar este repositorio.
- Una carpeta de trabajo donde el asistente pueda guardar los archivos de tu
  empresa.

La metodología se inspira en **Scaling Up** de Verne Harnish. ScaleUp ofrece
guía metodológica; no ofrece asesoría financiera ni legal.
