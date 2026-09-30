---
epic_id: E78
title: Instalación, runtime y recuperación verificables
status: planned
closure_disposition: active
created: 2026-09-12
updated: 2026-09-12
depends_on: []
related: [E10, E41, E42, E67, E79, E81]
source_findings: [H01, H02, H05, H09, H10]
---

# Scope E78

## Objetivo y autoridad

Una versión identificable completa el recorrido instalar → primera operación → reiniciar → actualizar → recuperar, conservando datos y plataforma elegida.

Reparación transversal de las rutas existentes de E10/E41. E78 es el único propietario de esta implementación correctiva; E10/E41 consumen sus recibos y E42 conserva la aceptación en equipos limpios.

**Estado:** planificado, implementación no iniciada. Los requisitos y pruebas son trabajo pendiente. Esta épica se registra en el backlog local canónico; no se afirma que exista un ticket remoto. [Programa de reparación](../../../governance/pilot-readiness-2026-09-12.md).

## Dentro

- Un intérprete y una versión de producto coherentes en instalador, lanzador, API, diagnóstico y actualización.
- Artefacto portable con código, conocimiento permitido, recursos estáticos y dependencias declaradas.
- Lifecycle real, actualización transaccional, respaldo consistente y recuperación demostrada.
- Preflight y diagnóstico accionable para todas las rutas soportadas, con pruebas fuera del checkout.

## Fuera

- Crear un nuevo asesor, servidor central o instalador gráfico completo.
- Publicar paquetes o declarar Windows nativo/macOS calificados sin sus recibos E42.
- Crear entornos duplicados, instalar con pip global o descargar dependencias de manera implícita en modo anunciado como offline.

## Decisiones y restricciones de diseño

1. El lanzador resuelve el intérprete del runtime instalado; nunca cae silenciosamente al Python global. El mínimo declarado será Python 3.11 mientras exista `enum.StrEnum`, con prueba de ese mínimo.
2. Un manifiesto/recibo identifica versión, commit, plataforma, intérprete, destino y modo; la matriz compatible y las dependencias reproducibles forman parte del artefacto.
3. El runtime web se gestiona como un proceso local verificable. La conversación sigue perteneciendo al agente elegido; `start` no puede declarar encendido ese agente sin observarlo.
4. El mecanismo de respaldo es reutilizable por E79, pero E79 decide cómo asignar y migrar datos entre empresas.
5. La instalación de dependencias puede requerir red: debe declararse y fallar antes de activar una versión. Una variante offline sólo se anuncia cuando incluye y verifica sus dependencias.

Estos límites guían el diseño de historia; cualquier cambio que afecte contrato de empresa, migración o promesa pública debe quedar motivado y con prueba negativa. No se crea una segunda autoridad de estado o una capacidad pública paralela.

## Historias, requisitos y dependencias

El orden numérico identifica historias, no impone un orden topológico. Las dependencias de la tabla son obligatorias; las dependencias a épicas significan su entrega verificada. Las referencias relacionadas son coordinación, no un bloqueo artificial para reparar defectos existentes.

| Historia | Entrega | Tamaño | Dependencias duras | Estado | Requisito |
|---|---|:---:|---|---|---|
| S78.1 | Unificar intérprete, mínimo Python y preflight | M | Sin bloqueo técnico previo | planned | REQ-E78-001 |
| S78.2 | Calificar el artefacto completo y su identidad | M | S78.1 | planned | REQ-E78-002 |
| S78.3 | Actualizar y revertir el código realmente ejecutado | L | S78.1, S78.2, S78.4, S78.5 | planned | REQ-E78-003 |
| S78.4 | Arranque, salud y parada observables | L | S78.1, S78.2 | planned | REQ-E78-004 |
| S78.5 | Respaldar y restaurar estado consistente | L | S78.1, S78.2 | planned | REQ-E78-005 |
| S78.6 | Diagnóstico y recorrido integrados para soporte | M | S78.3, S78.4, S78.5 | planned | REQ-E78-006 |

### S78.1 — Unificar intérprete, mínimo Python y preflight

**Componentes/archivos a inspeccionar:** install.sh; scripts/escala-python; pyproject.toml; escala-skills/escala/SKILL.md.

Como empresario quiero que la primera operación use el entorno que se acaba de instalar.

**Criterios de aceptación — REQ-E78-001:**

- [ ] Usar/reutilizar `.venv` y resolver el intérprete desde el recibo de instalación, independientemente del cwd y del user-site del desarrollador.
- [ ] Alinear `requires-python`, preflight y mensajes con los imports reales; rechazar una versión incompatible antes de modificar destinos.
- [ ] Detectar agente ausente, runtime incompleto y falta de red con causa y siguiente acción; conservar plataformas no seleccionadas.

**Validación:** Positiva: instalar y ejecutar Welcome con user-site deshabilitado desde otra carpeta. Negativas: Python 3.10, dependencia ausente, PATH con otro Python y agente no instalado.

**Evidencia exigida:** Un recibo muestra el mismo intérprete en instalación y primera operación; no se crean entornos adicionales.

**Razón de secuencia:** Fija la dependencia común antes de empaquetar o recuperar.

### S78.2 — Calificar el artefacto completo y su identidad

**Componentes/archivos a inspeccionar:** validators/public_export.py; scripts/verify_portable_bundle.py; escala_server/lifecycle/installer.py; escala_server/__main__.py; recursos de conocimiento/static.

Como instalador quiero recibir todos los archivos necesarios sin depender del repositorio fuente.

**Criterios de aceptación — REQ-E78-002:**

- [ ] Unificar la selección de recursos para evitar que el ZIP lifecycle omita coaching, plantillas o recursos necesarios; inventariar variantes deliberadamente limitadas.
- [ ] Ejecutar módulos y abrir un dashboard desde un directorio externo, sin editable install del checkout fuente ni PYTHONPATH heredado.
- [ ] Usar versiones de dependencias reproducibles y una identidad de release consistente; documentar traslado del bundle, reinstalación y enlaces rotos.

**Validación:** Positiva: extracción e instalación en directorio con espacios, ejecución de coaching y servidor. Negativas: falta de YAML/static/módulo, hash alterado y carpeta movida sin reparación.

**Evidencia exigida:** Inventario, hashes, versión y recursos ejecutados pertenecen al mismo artefacto; no se declara funcional una variante incompleta.

**Razón de secuencia:** Evita atribuir al runtime archivos aportados por la máquina de desarrollo.

### S78.3 — Actualizar y revertir el código realmente ejecutado

**Componentes/archivos a inspeccionar:** update.sh; install.sh; escala-skills/escala-update/SKILL.md; escala_server/lifecycle/updates.py.

Como empresario quiero actualizar sin perder mi configuración ni quedar entre dos versiones.

**Criterios de aceptación — REQ-E78-003:**

- [ ] Persistir y reutilizar la plataforma/modo elegido; el actualizador nunca llama al instalador sin sus argumentos obligatorios.
- [ ] Preparar y verificar candidato antes de activar; reemplazar el código ejecutable y no sólo copiar el artefacto o cambiar metadata.
- [ ] Integrar respaldo/restauración de S78.5; revertir código y datos de forma compatible tras fallo, conservando la versión anterior hasta verificar la nueva.
- [ ] Mantener `git pull --ff-only` únicamente en la ruta de desarrollo; el usuario del bundle no necesita Git para actualizarlo.

**Validación:** Positiva: V1 responde un valor de prueba, V2 otro y rollback vuelve a V1. Negativas: descarga interrumpida, candidato corrupto, activación fallida y argumentos faltantes.

**Evidencia exigida:** Se observa la versión activa mediante su comportamiento e identidad, además de comprobar estado empresarial y plataforma preservados.

**Razón de secuencia:** Depende del artefacto; S78.5 es un requisito de integración antes de cerrar esta historia.

### S78.4 — Arranque, salud y parada observables

**Componentes/archivos a inspeccionar:** escala_server/lifecycle/runtime.py; escala_server/lifecycle/cli.py; escala_server/lifecycle/scheduler.py; escala_server/__main__.py.

Como empresario quiero que 'funcionando' signifique que puedo usar el servicio.

**Criterios de aceptación — REQ-E78-004:**

- [ ] Arrancar el proceso local correspondiente, observar identidad/PID/puerto y comprobar disponibilidad de aplicación y base; usar un namespace sintético para la prueba de lectura/escritura.
- [ ] Un marker, proceso muerto, puerto ocupado por otro servicio o aplicación inexistente nunca equivalen a `healthy`.
- [ ] Arranque repetido es idempotente; stop sólo detiene el proceso propio; tiempos de espera acotados y errores recuperables.
- [ ] Los schedules usan el mismo comando/interprete real y no simulan su instalación o ejecución.

**Validación:** Positiva: proceso real sirve health y guarda/recupera dato sintético. Negativas: app/DB ausentes, muerte inesperada, marker obsoleto y puerto ocupado.

**Evidencia exigida:** El proceso desaparece al detenerlo y el estado posterior refleja la realidad; las pruebas limpian todos los procesos.

**Razón de secuencia:** Permite verificar activación de versiones y elimina diagnósticos falsamente verdes.

### S78.5 — Respaldar y restaurar estado consistente

**Componentes/archivos a inspeccionar:** escala_server/lifecycle/updates.py; escala_server/schema.py; persistencia YAML/Markdown consumida por lifecycle.

Como empresario quiero recuperar mi trabajo tras una interrupción o migración.

**Criterios de aceptación — REQ-E78-005:**

- [ ] Respaldar SQLite de forma consistente, incluyendo escrituras en WAL mediante mecanismo adecuado; conservar los documentos y consentimientos asociados.
- [ ] Manifestar versión de esquema, empresa/alcance opaco y checksums; restaurar de forma atómica sin mezclar snapshots.
- [ ] Ensayar migración fallida, respaldo corrupto y espacio/permisos insuficientes; mantener intacta la fuente hasta aceptar la recuperación.
- [ ] Exponer el mecanismo a E79 sin decidir automáticamente la empresa de datos legados ambiguos.

**Validación:** Positiva: snapshot durante escrituras y restauración en ubicación nueva con igualdad de datos confirmados. Negativas: corte a mitad, WAL pendiente, corrupción y permisos.

**Evidencia exigida:** Recibo de restauración compara datos/esquemas y no sólo existencia del ZIP; datos reales y backups no entran en Git.

**Razón de secuencia:** Puede implementarse junto con S78.4 tras el artefacto; integra obligatoriamente con S78.3.

### S78.6 — Diagnóstico y recorrido integrados para soporte

**Componentes/archivos a inspeccionar:** escala-skills/escala-health/SKILL.md; README.md; docs/e41-local-installation.md; escala_server/README.md; tests de instalación/lifecycle.

Como usuario o soporte quiero una explicación comprobable de lo que falló y cómo recuperarlo.

**Criterios de aceptación — REQ-E78-006:**

- [ ] Eliminar instrucciones de pip global, conteo de antiguos skills y comandos incompatibles; comprobar la única puerta pública `escala`.
- [ ] Entregar salida estructurada y resumen empresarial con versión, capacidades reales y error accionable, sin datos de empresa.
- [ ] Ejecutar el recorrido completo desde el artefacto; separar resultados de fixtures, Linux de desarrollo y hardware real E42.
- [ ] Pasar a E81 datos técnicos mínimos para soporte y a E42 procedimientos reproducibles.

**Validación:** Positiva: instalar → ejecutar → guardar → reiniciar → actualizar → recuperar. Negativas: cada H01/H02/H05 reaparece sembrado y el diagnóstico lo identifica.

**Evidencia exigida:** Recibo de integración con commit/hash y pruebas de no pérdida; documentación y comandos se ejecutan tal como están escritos.

**Razón de secuencia:** Cierra las uniones entre componentes antes de solicitar aceptación externa.

## Hitos y seguimiento

| Hito | Historias | Condición verificable | Fecha/real |
|---|---|---|---|
| M1 | S78.1, S78.2 | Artefacto y primera operación aislados del entorno del desarrollador. | Por planificar / pendiente |
| M2 | S78.3, S78.4, S78.5 | Proceso real, actualización efectiva y recuperación de datos comprobados. | Por planificar / pendiente |
| M3 | S78.6 | Recorrido integrado y handoff reproducible a E42/E81. | Por planificar / pendiente |

Los cruces entre componentes se prueban antes del cierre final, mediante el último hito de integración. Se registran esfuerzo real y diferencias respecto del tamaño al cerrar cada historia; no se inventa velocidad ni duración.

## Criterios de terminación

- [ ] Los seis requisitos tienen evidencia exacta y trazable al commit/artefacto ejecutado.
- [ ] Casos positivos, negativos y de recuperación aplicables pasan en el límite real que se afirma proteger.
- [ ] Todos los hallazgos asignados tienen disposición explícita; no se considera reparación una etiqueta o un fixture verde.
- [ ] Documentación, interfaz, comandos y capacidades anunciadas coinciden con el comportamiento observado.
- [ ] Una revisión independiente comprueba correctness, regresiones y fronteras de datos al implementar; no se presume realizada en esta planificación.
- [ ] Retrospectiva y handoff a las épicas relacionadas actualizan el backlog sin alterar sus gates de aceptación.
- [ ] La evidencia humana/hardware exigida está presente o se conserva el gate pendiente; no se fabrica para cerrar.

## Riesgos y mitigaciones

- Un simulacro de proceso vuelve a producir verde: el recibo exige PID, respuesta HTTP y persistencia real.
- La restauración sólo verifica metadata: comparar contenido y comportamiento de V1/V2 después de rollback.
- Nuevas dependencias cambian el bundle mientras E80 añade PDF: coordinar cambios en pyproject/manifiesto y repetir el recorrido integrado.

## Cómo iniciar y cerrar

Al iniciar una historia: leer este scope y [acceptance.md](acceptance.md), reproducir la línea base pertinente, diseñar el cambio acotado, implementar, verificar, revisar y documentar resultado. La creación de estos archivos no ejecuta ese ciclo ni autoriza contactar participantes o distribuir el producto.

La planificación sigue la estructura de `rai-epic-plan`. No existía un diseño específico previo para esta reparación: se parte de evidencia reproducida y los contratos existentes referenciados. Si el grafo o la sesión RaiSE no están disponibles, los artefactos locales siguen siendo revisables; no se simulan resultados de esas herramientas.
