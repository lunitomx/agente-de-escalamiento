---
epic_id: "E42"
grounded_in:
  - "E36 master acceptance ledger"
  - "E37-E41 evidence and retrospectives"
  - "current ScaleUp pipelines, memory, coaching, meetings, cash and lifecycle"
---

# Diseño E42 — Cómo se comprobará el producto

## Hallazgos del producto actual

| Área | Lo que ya existe | Qué comprobará E42 |
|---|---|---|
| Instalación | Paquete, runtime, actualización, rollback y scheduling local | Que funcione en máquinas limpias y no solo en simulación. |
| Documentos | Ingesta local y carpeta opcional de intercambio | Que acepte archivos reales sin convertir la carpeta compartida en autoridad. |
| Cash | Lectura financiera y reporte ejecutivo | Que interprete un workbook y preserve dudas y procedencia. |
| Reuniones | Intake y análisis de dailies/weeklies | Que conecte hallazgos, compromisos y seguimiento sin inferencias psicológicas. |
| Estrategia | Coaching, OPSP y evidencia de voz del cliente | Que pregunte antes de afirmar y cite evidencia disponible. |
| Cockpit | Diagnóstico y guía ejecutiva | Que muestre dolor, evidencia y siguiente acción de forma comprensible. |
| Skills | Catálogo, pipelines y golden cases | Que cada skill entregado tenga invocación actual, caso positivo y negativo. |

## Enfoque

E42 no crea un sistema nuevo. Ensambla el producto existente en un recorrido,
registra lo que ocurre y confronta documentación contra comportamiento.

Cada resultado tendrá cinco respuestas:

1. qué se intentó;
2. con qué versión y plataforma;
3. qué ocurrió;
4. qué evidencia lo demuestra;
5. quién lo aceptó y con qué reserva.

## Paquetes de trabajo

| Paquete | Responsabilidad | Salida |
|---|---|---|
| Viaje empresarial | Ejecutar instalación, ingesta, análisis y seguimiento | Recorrido reproducible y observaciones. |
| Matriz de plataforma | Repetir en macOS y Windows limpios | Recibos de plataforma y versiones. |
| Inventario de skills | Relacionar skill, intención, casos y recibos | Catálogo técnico de verdad. |
| Escenarios negativos | Probar privacidad, daño, interrupción y no-network | Reporte de recuperación segura. |
| Catálogo empresarial | Traducir evidencia a lenguaje no técnico | Catálogo y PDF en español. |
| Aceptación | Revisar requisito por requisito con el dueño | Firma de aceptación o reservas abiertas. |

## Contrato de evidencia

La evidencia deberá indicar:

- identificador del requisito;
- plataforma y versión;
- tipo: sintética, hardware real o aceptación humana;
- archivos utilizados en forma redactada;
- resultado esperado y resultado observado;
- gates ejecutados;
- límites y preguntas abiertas;
- aprobación o reserva humana.

## Experiencia del empresario

El empresario nunca necesitará leer los recibos internos. Recibirá:

- una instrucción clara por paso;
- preguntas solamente cuando falte información;
- una explicación de lo observado;
- una acción sugerida;
- límites visibles;
- un catálogo final en español.

## Decisiones

- La qualification permanece local.
- Las máquinas limpias son la prueba de plataforma; una cadena de texto
  "windows" no sustituye hardware Windows.
- La aceptación humana se registra aparte de los gates.
- El catálogo se genera desde la matriz probada, no desde la lista de archivos.
- Los defectos encontrados no se maquillan: abren reparación y después se
  repite el escenario.
- Las métricas de claridad y utilidad son línea base, no promesas de E42.

## Riesgos de integración

- El flujo puede depender de artefactos existentes en el checkout de desarrollo.
- La matriz Windows puede revelar diferencias de rutas, permisos o scheduling.
- Un skill puede existir y pasar validación estructural sin producir valor real.
- El PDF puede desalinearse si se genera antes de cerrar la evidencia.
- La prueba con empresario puede revelar lenguaje todavía demasiado técnico.

## Relación con el roadmap agentic

E42 responde "¿qué tan bueno es ESCALA hoy?". E43-E46 solo podrán responder
"¿mejoró?" si esta línea base existe. Por eso E42 no incorpora agentes nuevos:
califica el producto actual y captura las medidas que utilizará el roadmap.
