---
document_status: ready_for_review
created: 2026-09-12
initiative: entrepreneur-pilot-readiness
epics: [E78, E79, E80, E81]
---

# Reparación y calificación del piloto de 20 empresarios

## Decisión y estado

El dueño solicitó documentar el trabajo necesario para reparar todos los hallazgos de la auditoría del proyecto. Se crean cuatro épicas planificadas, 24 historias, 24 requisitos y 24 casos de aceptación agrupados. No se ha implementado ninguna reparación ni se han reclutado participantes por esta planificación.

El estado de cada épica reside exclusivamente en su `scope.md`; [backlog.md](backlog.md) es el inventario ejecutable. Este programa organiza dependencias y evidencia, sin crear otra autoridad de estado.

| Épica | Resultado | Documentación |
|---|---|---|
| E78 | Instalación, runtime real, actualización y recuperación | [Brief](../work/epics/e78-reliable-installation-runtime-recovery/brief.md) · [Scope e historias](../work/epics/e78-reliable-installation-runtime-recovery/scope.md) · [Aceptación](../work/epics/e78-reliable-installation-runtime-recovery/acceptance.md) |
| E79 | Aislamiento por empresa, privacidad y frontera local | [Brief](../work/epics/e79-company-isolation-privacy-local-security/brief.md) · [Scope e historias](../work/epics/e79-company-isolation-privacy-local-security/scope.md) · [Aceptación](../work/epics/e79-company-isolation-privacy-local-security/acceptance.md) |
| E80 | Indicadores honestos, documentos y continuidad útil | [Brief](../work/epics/e80-evidence-backed-diagnostics-document-intake/brief.md) · [Scope e historias](../work/epics/e80-evidence-backed-diagnostics-document-intake/scope.md) · [Aceptación](../work/epics/e80-evidence-backed-diagnostics-document-intake/acceptance.md) |
| E81 | Piloto acompañado, cohorte de veinte y soporte medible | [Brief](../work/epics/e81-entrepreneur-pilot-qualification-support/brief.md) · [Scope e historias](../work/epics/e81-entrepreneur-pilot-qualification-support/scope.md) · [Aceptación](../work/epics/e81-entrepreneur-pilot-qualification-support/acceptance.md) |

## Línea base observada y límites

- Fecha: 2026-09-12. HEAD: `50e72f78758ea8422f627508028f9565e3a0ea70`. El checkout tenía cambios previos de skills de gobierno, manifiesto de fuentes y archivos locales; no es un recibo de release limpio.
- Entorno observado: Linux de desarrollo, `.venv` existente, Python 3.14.7; el Python de sistema observado es 3.12.3. No representa macOS ni Windows limpio.
- Pruebas seleccionadas: 119 pass y 1 fail. El fallo fue descarga de PyYAML/PyPI por DNS/red restringida en la prueba de instalación portable completa; se registra como limitación del entorno, no como regresión demostrada ni como éxito offline.
- Reproducciones adicionales usan sólo empresas, archivos y valores sintéticos en directorios temporales. No se ejecutó una cohorte ni se estimó una tasa real de abandono.
- `rai session open` y una consulta local al grafo fallaron por intento de escribir en una base de sólo lectura. No se obtuvieron patrones de secuencia; se continúa con los contratos locales según la alternativa documentada en el plan canónico. No se afirma haber creado tickets Jira ni publicado documentos remotos.
- La ruta pública recomendada usa un agente de terminal; los defectos de API/dashboard/lifecycle se delimitan a esas superficies. No se generaliza un fallo de un componente a todos los modos del producto.

## Registro hallazgo → reparación → aceptación

P1 significa corregir antes de usar datos reales o ampliar el piloto. P2 identifica fricción o brecha de evidencia que debe resolverse antes de afirmar autonomía. La prioridad no representa una explotación observada ni una probabilidad estadística.

| ID | Tipo / prioridad | Evidencia y límite | Propietario y prueba |
|---|---|---|---|
| H01 | Defecto reproducido / P1 | `install.sh` instala en `.venv`; `scripts/escala-python:7` ejecuta `python3`. Con user-site deshabilitado y Python del sistema: `ModuleNotFoundError: No module named 'pydantic'`. Además, `pyproject.toml` permite 3.10 pero Welcome importa `StrEnum` (3.11). | S78.1/S78.2; AT-E78-001/002 |
| H02 | Defecto reproducido / P1 | `update.sh:99` llama `bash install.sh`; esa llamada termina con código 2 porque no selecciona plataforma. El pull ocurre antes. Lectura adicional de lifecycle exige verificar activación real de código y rollback, no sólo metadata. | S78.3/S78.5; AT-E78-003/005 |
| H03 | Defecto reproducido / P1 | Dos empresas en una base: las hojas devuelven la última por categoría/herramienta; `MemoryEngine.get_relevant_facts` ignora `company_context`. Una consulta para A devuelve un hecho con fuente B. No demuestra cruce entre computadoras independientes. | S79.1/S79.2/S79.3; AT-E79-001/002/003 |
| H04 | Defecto reproducido / P1 | Guardar `pendiente` en las ocho claves de `SECTIONS` del OPSP devuelve estrategia 100/good y resumen global 100/good. Es completitud superficial que puede interpretarse como salud del negocio. | S80.1/S80.2/S80.6; AT-E80-001/002/006 |
| H05 | Defecto reproducido / P1 | `LifecycleRuntime.start/status` devuelve healthy sin directorio de aplicación ni base: sólo escribe/lee un marker. No es una prueba del proceso HTTP ni del agente conversacional. | S78.4/S78.6; AT-E78-004/006 |
| H06 | Limitación confirmada / P2 | `SourceRegistry.default().capability_for('reporte.pdf')` devuelve provider_unavailable/none. El agente podría tener herramientas distintas, pero la ingestión nativa no ofrece extracción. | S80.4/S80.5; AT-E80-004/005 |
| H07 | Promesa incompleta / P1 | README afirma permanencia local sin separar almacenamiento ESCALA de transmisión al modelo/historial del agente. La documentación oficial de Claude Code declara envío de datos al interactuar con el LLM. No se afirma filtración concreta ni se generaliza la retención entre proveedores. | S79.5/S79.6; AT-E79-005/006 |
| H08 | Defecto reproducido + configuración observada / P1 | El manejador static devuelve 200 para un archivo ficticio en carpeta hermana con el mismo prefijo, por `str.startswith`. CORS permite `*` y no hay control de acceso en ese manejador. El bind predeterminado es localhost. La reproducción fue del manejador; exigir HTTP real en la reparación. | S79.4; AT-E79-004 |
| H09 | Fricción documentada / P2 | Guía presupone Git, Python, uv, agente instalado y WSL2 en Windows. No se observaron empresarios abandonando por ello; es una hipótesis que exige medición. | S78.1/S78.6, S80.5, S81.1–S81.4 |
| H10 | Brecha de calificación / P1 para anunciar soporte | E42 conserva matriz sintética macOS/Windows y observación Linux no limpia; faltan recibos externos. Una prueba del instalador usa herramientas falsas; la prueba real de descarga no completó en este entorno. | S78.2/S78.6 y S81.1; E42/S42.1 y E68 conservan sus gates |
| H11 | Riesgo operativo inferido / P2 | Feedback local/manual protege privacidad, pero por sí solo no mide a quienes no instalan o abandonan. No hay una cohorte de veinte observada en esta auditoría. | S81.2–S81.6; AT-E81-002–006 |
| H12 | Revisión estructural + brecha de utilidad / P2 | `BusinessAdvisorHandler.ask` acepta contexto sin incorporarlo a la construcción de respuesta. Es la ruta standalone; no prueba que el LLM conversacional ignore contexto. Falta demostrar primera acción útil y continuidad real frente a la línea base. | S80.3/S80.5/S80.6 y S81.5 |

H01–H08 corresponden a los ocho hallazgos comunicados al dueño. H09–H11 formalizan los riesgos y límites discutidos en la conclusión. H12 conserva una observación adicional del código y la necesidad de medir utilidad, sin atribuir al modo conversacional un fallo no demostrado.

## Evidencia fuente

- [Instalador](../install.sh), [lanzador](../scripts/escala-python), [actualizador](../update.sh), [paquete Python](../pyproject.toml).
- [Lifecycle](../escala_server/lifecycle/runtime.py), [actualización y backup](../escala_server/lifecycle/updates.py), [bundle lifecycle](../escala_server/lifecycle/installer.py).
- [Memoria](../escala_server/memory_engine.py), [hojas de trabajo](../escala_server/daos/worksheet_dao.py), [handlers](../escala_server/handlers.py).
- [Dashboard](../escala_server/dashboard.py), [OPSP](../coaching/strategy_opsp/engine.py), [ingestión](../escala_server/workspace/ingestion.py), [asesor standalone](../escala_server/business_advisor.py).
- [Servidor](../escala_server/server.py), [CORS](../escala_server/cors.py), [guía del piloto](../PILOTO-EMPRESARIOS.md).
- [E42: viaje sintético y pendientes](../work/epics/e42-product-qualification-and-functional-catalog/evidence/s42.1-local-journey.md), [observación Linux no calificadora](../work/epics/e42-product-qualification-and-functional-catalog/evidence/s42.1-vps-linux-observation-2026-08-29.md).
- [Claude Code: flujo local y transmisión al modelo](https://code.claude.com/docs/en/data-usage#local-claude-code-data-flow-and-dependencies), consultado 2026-09-12. Verificar de nuevo por proveedor/modo al implementar la explicación de privacidad.
- [Python 3.11: StrEnum](https://docs.python.org/3.11/library/enum.html#enum.StrEnum), referencia de la incompatibilidad con el mínimo declarado 3.10.

## Reproducibilidad de la línea base

La primera selección ejecutó 95 pruebas (94 pass / 1 fail por red):

```bash
.venv/bin/python -m pytest tests/test_installer_targeting.py tests/test_public_skill_installation.py tests/test_e41_lifecycle.py tests/test_e52_welcome_persistence.py tests/test_escala_daos.py tests/test_business_advisor.py tests/test_portable_bundle_verifier.py -q --disable-warnings
```

La segunda selección ejecutó 25 pruebas (25 pass):

```bash
.venv/bin/python -m pytest tests/test_escala_server.py::TestRouter tests/test_escala_server.py::TestCompaniesHandler tests/test_escala_server.py::TestWorksheetsHandler tests/test_escala_server.py::TestDashboardHandler tests/test_workspace_ingestion.py -q --disable-warnings
```

Para repetir los casos adversariales, usar un directorio temporal y base nueva; nunca el estado real del usuario:

1. H01: ejecutar el lanzador con el Python del sistema y `PYTHONNOUSERSITE=1`, verificando primero que `.venv` sí contiene Pydantic. Resultado observado: import falla fuera del runtime preparado.
2. H02: ejecutar `bash install.sh` sin argumentos. Resultado observado: código 2 y solicitud de plataforma; no ejecutar un pull para reproducirlo.
3. H03: crear A/B, guardar dos versiones cash/power-of-one con identificadores distintos y consultar la hoja; agregar un hecho con fuente B y solicitar contexto A. Resultado: última hoja B y hecho B visible para A.
4. H04: guardar `{section: 'pendiente' for section in SECTIONS}` y consultar `DashboardHandler.summary()`. Resultado: strategy.score y overall.score iguales a 100, estado good.
5. H05: construir `InstallRequest` con install_root inexistente y data_root local válido; llamar start/status. Resultado: healthy y aplicación/base ausentes; llamar stop al terminar.
6. H06: consultar `SourceRegistry.default().capability_for('reporte.pdf')`. Resultado: provider_unavailable, adapter none.
7. H08: crear static/ y static-private/probe.txt con texto ficticio; invocar `_serve_static('/../static-private/probe.txt')` con salida en memoria. Resultado: código 200 y contenido del archivo hermano. La reparación debe demostrar además rechazo por HTTP real.

Los resultados son notas de observación del análisis, no nuevos tests de aceptación aprobados. Los casos AT de cada épica están pendientes y deben implementarse de forma que fallen ante la regresión correspondiente.

## Propiedad respecto de épicas existentes

| Épica existente | Reparación asignada | Qué conserva |
|---|---|---|
| E10 | E78 corrige lanzador, paquete, update y diagnóstico. | Puerta única y distribución portable; cierre sujeto a reparación y E42/E68. |
| E41 | E78 corrige ejecución/health/activación/recuperación; se reabre por H05 reproducido. | Contratos locales existentes y recualificación de sus requisitos afectados. |
| E37/E49/E52/E55 | E79/E80 consumen sus contratos y prueban integración. | Fuente/evidencia/consentimiento/intake; no se reabren por inferencia general. |
| E73 | E80 repara el resumen actual y define semántica de indicadores. | Recomendación/generación adaptativa de nuevos dashboards; reutiliza contrato E80. |
| E74 | E79 implementa identidad, aislamiento local y migración urgente. | ADR de colaboración, estado portable compartible y reconciliación; reutiliza resolver E79. |
| E42 | Recibe E78/E79/E80 para calificar el artefacto real. | Los ocho pasos, macOS/Windows limpios y aceptación humana; sus seis requisitos no se sustituyen. |
| E68 | Recibe casos semánticos E80 y observaciones E81. | Activación/paridad Codex/Claude y piloto trimestral; dos sesiones no equivalen a un trimestre. |
| E44/E45 | E81 consume aprendizaje/contraste existentes. | Ciclo de resultados y comparación de especialistas contra coach único. |
| E70 | Añade E81 como entrada de decisión. | Gate total y decisión humana de distribución, sin publicación automática. |

La separación en nuevas épicas permite reparar contratos actuales sin esperar bibliotecas o colaboración todavía planificadas. No hay una segunda implementación en E73/E74: sus scopes transfieren explícitamente el mínimo correctivo y conservan su extensión funcional.

## Secuencia y coordinación

```text
S78.1 → S78.2 → S78.4/S78.5 → S78.3 → S78.6 ───────────────┐
S79.1 → S79.2 → S79.3 (consume S78.5) ─┐                    │
S79.4 y S79.5 ─────────────────────────┴→ S79.6 ← S78.6     │
S80.1 → S80.2; S80.3 ← S79.2; S80.4 ← S79.5               │
                   └────────→ S80.5 → S80.6 ← S78.6/S79.6 ─┤
                                                         ↓
S81.1 (preparación) → S81.2 → S81.3 (3–5) → S81.4 (20) → S81.6
                                      └→ S81.5 (valor) ────┘
E42/E68: evidencias reales por artefacto/plataforma; E70: decisión total posterior.
```

E78/E79/E80 pueden comenzar por sus historias sin dependencias. E81 puede preparar protocolo; observar usuarios depende de las reparaciones y de autorización/disponibilidad externas. E42/E68 no dependen del cierre E81 para producir los recibos necesarios para observar usuarios: evitar esa dependencia circular.

| Superficie compartida | Responsable | Coordinación obligatoria |
|---|---|---|
| pyproject, manifiesto, instalador y lanzador | E78 | E80 propone dependencia PDF; E78 integra/fija y vuelve a verificar artefacto. |
| server/CLI/lifecycle | E78: proceso; E79: acceso/empresa | Acordar contrato antes de editar el mismo archivo; integrar en S79.6. |
| raíz/identidad de empresa y persistencia | E79 | E78 provee backup; E80 consume contexto validado; E74 extiende después. |
| dashboard, indicadores y preguntas | E80 | E79 provee aislamiento; E73 reutiliza contrato. |
| README y PILOTO-EMPRESARIOS | E81 consolida guía; E78/E79/E80 aportan secciones | Secuenciar ediciones; no sobrescribir cambios ajenos ni publicar afirmaciones sin evidencia. |

Esta tabla señala oportunidades de trabajo independiente para una ejecución futura; no implica que se hayan lanzado agentes o iniciado historias ahora.

## Gates de paso

1. **Preparación técnica:** E78–E80 verificadas, cero incidentes críticos de pérdida/cruce/exposición, caso de instalación y persistencia sobre el artefacto ofrecido, límites públicos corregidos.
2. **Cohorte acompañada:** 3–5 personas reales, evidencia por combinación ofrecida y consentimiento antes de documentos reales. Pasar a veinte requiere los criterios de S81.3 y decisión explícita.
3. **Cohorte autónoma:** veinte participantes distintos, contados desde recepción de instrucciones; incluir no iniciados y abandonos. Los objetivos de S81.4 se fijan antes de reclutar.
4. **Decisión:** informe real y aceptación de ampliar/iterar/detener. E42/E68/E70 mantienen sus exigencias completas; ninguna prueba local autoriza publicación o transferencia de datos.

Los objetivos de 18/20 instalaciones sin ayuda, 15/20 primeras acciones, 14/20 retornos y mediana de soporte ≤15 minutos son propuestas de producto, no predicciones. Informar numerador/denominador, ventana, asistencia y casos sin observación. La segunda sesión se observa entre los días 5 y 10; el horizonte no sustituye el ciclo trimestral de E68.

## Cierre de la planificación

La documentación está completa cuando todos los hallazgos tienen propietario, cada historia tiene aceptación positiva/negativa y evidencia, las dependencias no tienen ciclos y los índices canónicos enlazan los scopes. El cierre de esta tarea documental no cambia `planned` por `complete` en las cuatro épicas.

## Verificación documental realizada — 2026-09-12

- Inventario de scopes: pass mediante `.venv/bin/python -m scripts.check_scope_inventory --repo . --inventory governance/scope-inventory.yaml --closure-policy governance/closure-dispositions.yaml`.
- Contrato de gobierno: pass mediante `.venv/bin/python -m scripts.check_governance_contract --repo . --closure-policy governance/closure-dispositions.yaml --identity-policy governance/epic-identities.yaml --format json`.
- Pruebas existentes de inventario, cierres y contrato: **107 pass** con `.venv/bin/python -m pytest tests/test_scope_inventory.py tests/test_epic_closure_governance.py tests/test_governance_contract.py -q --disable-warnings`.
- Comprobación documental: **13 documentos nuevos**, 4 épicas, 24 historias, 24 requisitos, 24 grupos de casos, **64 enlaces locales válidos** y 12 hallazgos cubiertos. Dependencias revisadas sin ciclos entre las 24 historias nuevas y 36 épicas canónicas/legadas alcanzadas.
- La invocación directa del script de inventario falló porque no añadía la raíz al import path; la ejecución como módulo indicada arriba pasó. No se modificó el script para esta tarea documental.

Estas comprobaciones validan la planificación y su integración al backlog. Las reparaciones de producto, pruebas AT y observaciones con empresarios permanecen pendientes en sus épicas.
