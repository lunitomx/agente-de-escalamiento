---
epic_id: "E56"
status: "completed"
title: "Un solo orquestador y catálogo canónico de capacidades"
depends_on:
  - "E42 — catálogo funcional calificado"
  - "E49 — experiencia diagnóstica y evidencia"
related:
  - "E55 — onboarding multifuente y conciliación"
  - "E52 — memoria conversacional"
---

# E56 — Un solo orquestador y catálogo canónico de capacidades

## Resultado empresarial

Una persona no técnica instala **ESCALA** y conversa con un único agente. No
necesita conocer, buscar ni invocar decenas de comandos. El orquestador entiende
su intención, consulta el estado y la evidencia disponibles, y ejecuta la
capacidad correcta —o explica con claridad qué información falta— sin revelar
la complejidad interna del catálogo.

## Problema comprobado

El repositorio contiene 62 skills canónicos `escala-*` y 39 skills legados
`scaleup-*`. Treinta y ocho pares son la misma capacidad bajo distinto prefijo;
`execution-rockefeller` es el único legado sin equivalente `escala-*`. Además,
los mismos contenidos aparecen en varios directorios de agentes. El instalador
actual enlaza los 62 skills uno por uno, por lo que una instalación expone una
superficie técnica que contradice el producto de un solo agente orquestador.

## Hipótesis

Si ESCALA tiene una entrada pública única, un registro canónico y una política
explícita para conservar, internalizar, compatibilizar o retirar cada capacidad,
el empresario obtiene una experiencia simple sin perder las capacidades ya
construidas ni romper instalaciones existentes.

## Métricas de éxito

- Una conversación natural puede iniciar, retomar, diagnosticar o dirigir al
  siguiente paso sin que el usuario nombre un skill o slash-command.
- Cada capacidad tiene exactamente una implementación canónica, dueño técnico,
  contrato de entrada/salida y estado de ciclo de vida documentado.
- Ningún alias legado ejecuta una segunda implementación; durante la ventana de
  compatibilidad se enruta al mismo contrato canónico o comunica su retiro.
- La instalación distribuye sólo el front door y las dependencias permitidas;
  los especialistas internos no se convierten en comandos del empresario.
- La paridad de los artefactos distribuidos se verifica de forma determinista y
  una deriva o un nombre huérfano falla antes de publicar.

## Tamaño y secuencia

**L, en seis historias.** Primero se inventaría y decide; después se introduce
el orquestador y una fuente única; sólo entonces se migran y retiran duplicados.
No se borra un skill por coincidencia de nombre ni se mezcla este trabajo con el
onboarding multifuente de E55.

## Decisiones que E56 debe cerrar

1. Qué capacidades siguen siendo procedimientos independientes y cuáles deben
   vivir como módulos internos o memoria/proceso del orquestador.
2. El contrato público de `escala`: lenguaje natural primero, con aliases de
   compatibilidad limitados y documentados.
3. La fuente de verdad del catálogo, el mecanismo de empaquetado por plataforma
   y la fecha/condición para retirar `scaleup-*`.

## No-Gos

- No reescribir los modelos de Cash, People, Strategy, Execution, memoria o
  evidencia; E56 reorganiza sus puntos de entrada, no sus metodologías.
- No eliminar capacidades ni datos de usuario antes de tener inventario,
  migración, pruebas y una ruta de regreso.
- No construir un router que simule certeza: si faltan datos o consentimiento,
  debe pedirlos o declarar el límite.
- No introducir conectores, OAuth, sincronización remota ni nuevas
  automatizaciones. Esas capacidades se planean y validan en sus propias épicas.
- No mezclar E56 con E55: E55 decide y concilia hechos de negocio; E56 decide
  cómo el agente llega a esas capacidades.

## Bitter Pill

Para cada skill se preguntará: **si el modelo tuviera memoria real del negocio,
¿seguiría haciendo falta como procedimiento explícito?** Sólo se mantiene como
capacidad visible o invocable cuando aporta un contrato estable, estado,
validación, evidencia, seguridad o un flujo que el usuario reconoce. Los demás
se internalizan o retiran con recibo de decisión.
