---
title: "ESCALA aprende sin volverse una caja negra"
status: "proposed"
created: "2026-07-22"
sequence: ["E42", "E43", "E44", "E45", "E46"]
---

# ESCALA aprende sin volverse una caja negra

## Veredicto de producto

Sí hay valor real en incorporar reflexión, herramientas, planificación y
colaboración entre especialistas. El valor no está en decirle al empresario que
hay muchos agentes trabajando. Está en que ESCALA:

1. entienda mejor la pregunta antes de responder;
2. use los documentos reales de la empresa;
3. detecte contradicciones y datos faltantes;
4. presente una recomendación clara, explicable y accionable;
5. dé seguimiento y aprenda si esa recomendación funcionó.

La experiencia debe seguir sintiéndose como hablar con un solo coach. La
complejidad queda detrás del producto.

## Lo que no sería valioso

- Ejecutar varios agentes para preguntas sencillas.
- Producir respuestas más largas sin mejorar la decisión.
- Llamar "aprendizaje" a guardar todo lo que el usuario dice.
- Cambiar skills o recomendaciones automáticamente.
- Inferir personalidad, desempeño o intención de empleados desde reuniones.
- Sacar información de la máquina para entrenar o mejorar el sistema.
- Convertir Drive o OneDrive en la autoridad del sistema.

## Principios no negociables

- **Un solo coach para el empresario:** el sistema puede usar especialistas,
  pero entrega una sola respuesta.
- **Evidencia antes que seguridad aparente:** cada afirmación importante muestra
  de dónde salió o reconoce que falta información.
- **Preguntar es parte del producto:** cuando no hay evidencia, ESCALA pregunta;
  no rellena huecos.
- **Local-only:** documentos, memoria, grafo y resultados permanecen en la
  máquina donde se instaló ESCALA.
- **Aprobación humana:** ninguna mejora modifica automáticamente conocimiento,
  prompts, skills o código.
- **Aprendizaje reversible:** toda mejora aprobada conserva versión, evidencia y
  forma de regresar.
- **Lenguaje empresarial:** la interfaz habla de objetivos, decisiones, riesgos,
  responsables y resultados; no de grafos, modelos o procesos internos.

## Secuencia de épicas

| Orden | Épica | Promesa para el empresario | Razón de la secuencia |
|---:|---|---|---|
| 1 | E42 — Producto probado y catálogo verdadero | "Puedo instalarlo y comprobar qué hace realmente." | Primero se mide la situación actual. |
| 2 | E43 — Respuestas confiables antes de recomendar | "Entiende mi pregunta, usa mis datos y revisa su respuesta." | Une planificación, herramientas y reflexión en una experiencia visible. |
| 3 | E44 — Aprendizaje a partir de resultados | "Recuerda qué decidimos y comprueba si funcionó." | El sistema solo puede aprender cuando existe seguimiento real. |
| 4 | E45 — Especialistas bajo demanda | "Cuando el problema cruza varias áreas, consulta al equipo adecuado." | Multi-agente solo después de tener evidencia y seguimiento. |
| 5 | E46 — Mejora gobernada del producto | "ESCALA propone mejoras basadas en uso real, pero yo conservo el control." | La auto-mejora llega al final, cuando ya puede probarse y medirse. |

No se abrirán las cinco épicas al mismo tiempo. E42 se inicializa ahora; E43 se
abre después de obtener la línea base. E44-E46 permanecen como roadmap hasta que
el gate anterior demuestre valor.

---

# E43 — Respuestas confiables antes de recomendar

## Promesa

Ante una pregunta importante, ESCALA define qué decisión se está tomando,
identifica qué información necesita, consulta los archivos locales adecuados,
revisa sus propios hallazgos y entrega una recomendación clara.

## Historias propuestas

| ID | Historia en lenguaje de negocio | Qué recibe el empresario |
|---|---|---|
| S43.1 | Entender la decisión antes de empezar | Confirmación breve del objetivo, área afectada y resultado esperado. |
| S43.2 | Reunir la evidencia necesaria | Lista simple de documentos encontrados, datos usados y datos faltantes. |
| S43.3 | Elegir las herramientas correctas | ESCALA usa transcripts, workbooks, contexto y tareas sin pedir formatos artificiales. |
| S43.4 | Revisarse antes de responder | Detecta cálculos dudosos, contradicciones, afirmaciones sin fuente y preguntas omitidas. |
| S43.5 | Presentar una respuesta ejecutiva | "Qué veo, por qué importa, qué no sé y qué haría ahora". |
| S43.6 | Probarlo en las cuatro decisiones | Casos completos de People, Strategy, Execution y Cash, con fallas sembradas. |

## Criterios de terminación

- Toda recomendación importante cita evidencia o declara qué información falta.
- Una inconsistencia financiera sembrada es detectada antes de mostrar el
  análisis.
- Una contradicción entre dos reuniones se presenta como contradicción, no como
  hecho.
- Las preguntas aparecen de una en una y explican por qué son necesarias.
- Una respuesta sencilla no muestra el proceso interno ni usa especialistas
  innecesarios.
- La respuesta final se puede leer en menos de cinco minutos.
- No se crea autoridad fuera de la base local de la máquina instaladora.

## Métricas de valor

- Porcentaje de recomendaciones con evidencia visible.
- Porcentaje de errores sembrados detectados antes de responder.
- Número de preguntas necesarias para llegar a una recomendación útil.
- Tiempo hasta la primera acción clara.
- Calificación del empresario: claridad, confianza y utilidad.

## Hitos

1. **Caso Cash completo:** pregunta, workbook, revisión y recomendación.
2. **Caso Weekly completo:** tres reuniones, contradicción y seguimiento.
3. **Cuatro decisiones:** People, Strategy, Execution y Cash pasan escenarios
   positivos y negativos.
4. **Aceptación empresarial:** el resultado es comprensible sin explicar la
   arquitectura interna.

## Fuera de alcance

- Aprender automáticamente de resultados posteriores; corresponde a E44.
- Usar varios especialistas; corresponde a E45.
- Modificar skills o código; corresponde a E46.

---

# E44 — Aprendizaje a partir de resultados

## Promesa

ESCALA no solo recuerda lo que recomendó. Registra qué decidió el empresario,
quién quedó responsable, qué resultado se esperaba y qué ocurrió después.

## Historias propuestas

| ID | Historia en lenguaje de negocio | Qué recibe el empresario |
|---|---|---|
| S44.1 | Convertir recomendaciones en decisiones | Registro de aceptada, rechazada o pendiente, con motivo y evidencia. |
| S44.2 | Dar seguimiento en el ritmo correcto | Preguntas automáticas en la daily, weekly, mensual o trimestral adecuada. |
| S44.3 | Comparar expectativa contra resultado | Una revisión que muestra qué cambió, qué no y qué sigue incierto. |
| S44.4 | Convertir resultados en aprendizaje | Lecciones con fuente, confianza, fecha y aprobación humana. |
| S44.5 | Ajustar la confianza de lo aprendido | Los aprendizajes confirmados ganan peso; los desmentidos o viejos lo pierden. |
| S44.6 | Mostrar qué está funcionando | Vista ejecutiva de decisiones, acciones, resultados y aprendizajes pendientes. |

## Criterios de terminación

- Una recomendación puede seguirse hasta su decisión, acción, responsable y
  resultado.
- ESCALA pregunta por el resultado en el momento correcto sin perseguir al
  usuario en cada conversación.
- El sistema separa correlación de causalidad y no afirma "esto funcionó por X"
  sin evidencia.
- El empresario puede corregir o rechazar un aprendizaje.
- Ningún aprendizaje sensible sobre una persona se promueve sin consentimiento.
- People no utiliza lenguaje clínico ni inferencias psicológicas.
- El dashboard distingue decisiones abiertas, acciones vencidas, resultados y
  aprendizajes por confirmar.

## Métricas de valor

- Porcentaje de recomendaciones que terminan en una decisión explícita.
- Porcentaje de acciones con responsable y fecha.
- Porcentaje de resultados revisados dentro de su cadencia.
- Aprendizajes confirmados, rechazados y vencidos.
- Reducción de recomendaciones repetidas que no producen acción.

## Hitos

1. **Un ciclo completo:** recomendación → decisión → acción → resultado.
2. **Ritmos empresariales:** seguimiento integrado a daily, weekly y trimestre.
3. **Memoria confiable:** aprendizaje revisable, corregible y con vigencia.
4. **Cuatro decisiones:** al menos un ciclo real por People, Strategy,
   Execution y Cash.

## Fuera de alcance

- Modificar la metodología por una sola experiencia.
- Evaluar empleados automáticamente.
- Comparar empresas entre sí o enviar información a un servicio central.

---

# E45 — Especialistas bajo demanda

## Promesa

Cuando una situación cruza varias áreas, ESCALA reúne a los especialistas
adecuados, confronta sus conclusiones y entrega una sola recomendación ejecutiva.
Las preguntas sencillas siguen siendo rápidas.

## Historias propuestas

| ID | Historia en lenguaje de negocio | Qué recibe el empresario |
|---|---|---|
| S45.1 | Distinguir preguntas simples de problemas complejos | Respuesta directa cuando no hace falta un equipo; explicación breve cuando sí. |
| S45.2 | Asignar especialistas por decisión | Participan solo People, Strategy, Execution o Cash que aporten valor. |
| S45.3 | Incorporar una voz crítica | Un rol busca supuestos débiles, contradicciones y riesgos omitidos. |
| S45.4 | Verificar números y fuentes | Un rol confirma cálculos, periodos y procedencia antes de la síntesis. |
| S45.5 | Resolver desacuerdos | ESCALA muestra qué está acordado, dónde existe duda y qué dato la resolvería. |
| S45.6 | Entregar una sola recomendación | Resumen ejecutivo con decisión, alternativas, riesgo, acción y seguimiento. |

## Criterios de terminación

- Las preguntas sencillas se resuelven sin activar el equipo completo.
- Los especialistas reciben únicamente el contexto que necesitan.
- El verificador puede bloquear una conclusión sin evidencia.
- Los desacuerdos no se esconden ni se convierten en una respuesta promedio.
- El empresario recibe una sola voz y no una conversación interna entre
  agentes.
- El caso de prueba cruza al menos tres decisiones, por ejemplo: caída de caja
  causada por precios, inventario, disciplina comercial y responsabilidades.
- Existen límites de intentos y condiciones claras para detenerse y preguntar.

## Métricas de valor

- Problemas complejos donde la revisión detectó un riesgo omitido.
- Diferencia de calidad frente a una sola respuesta, evaluada por empresarios.
- Casos simples resueltos sin colaboración innecesaria.
- Tiempo adicional de análisis frente al valor percibido.
- Desacuerdos resueltos por evidencia y desacuerdos que requirieron al dueño.

## Hitos

1. **Router sencillo:** diferencia correctamente simple vs. complejo.
2. **Primer equipo útil:** especialista, crítico y verificador trabajan sobre un
   caso Cash + Execution.
3. **Caso transversal:** tres o cuatro decisiones con desacuerdo explícito.
4. **Aceptación empresarial:** una sola respuesta, clara y superior a la línea
   base de E42.

## Fuera de alcance

- Ejecutar siempre varios agentes.
- Crear "personalidades" decorativas sin responsabilidad verificable.
- Dar acceso completo a todos los especialistas.
- Ocultar incertidumbre para producir consenso.

---

# E46 — Mejora gobernada del producto

## Promesa

ESCALA identifica problemas repetidos y propone cómo mejorar sus preguntas,
explicaciones o skills. Antes de cambiar, demuestra el problema, prueba la
solución y solicita aprobación.

## Historias propuestas

| ID | Historia en lenguaje de negocio | Qué recibe el empresario o equipo de producto |
|---|---|---|
| S46.1 | Recibir señales de mejora | Reúne bug reports anónimos, resultados fallidos y aprendizajes de clases. |
| S46.2 | Detectar patrones repetidos | Agrupa problemas semejantes sin copiar datos de una empresa. |
| S46.3 | Crear una propuesta revisable | Problema, evidencia, skill afectado, cambio sugerido e impacto esperado. |
| S46.4 | Probar antes y después | Casos conocidos muestran si la propuesta mejora sin romper otros flujos. |
| S46.5 | Aprobar, versionar y revertir | Ningún cambio se aplica sin aprobación; todo cambio puede deshacerse. |
| S46.6 | Completar un ciclo real de mejora | Señal real → propuesta → prueba → aprobación → medición posterior. |

## Criterios de terminación

- Una señal nunca contiene nombres, archivos empresariales, cifras o fragmentos
  de reuniones sin autorización explícita.
- El sistema distingue un problema aislado de un patrón repetido.
- Toda propuesta apunta a evidencia y a un comportamiento que puede medirse.
- Ningún cambio se aplica automáticamente.
- Los casos positivos y negativos pasan antes de presentar la propuesta como
  lista para aprobación.
- Existe una versión anterior y un procedimiento de reversión probado.
- Después de aplicar, se mide si el problema realmente disminuyó.

## Métricas de valor

- Señales convertidas en problemas reproducibles.
- Propuestas que mejoran casos sin provocar regresiones.
- Propuestas aprobadas, rechazadas o devueltas por falta de evidencia.
- Reducción del problema después de la mejora.
- Tiempo desde señal repetida hasta propuesta revisable.

## Hitos

1. **Señales seguras:** bugreport, E1801 y resultados de E44 convergen sin datos
   empresariales.
2. **Propuesta comprobable:** primer cambio con evidencia y casos antes/después.
3. **Promoción gobernada:** aprobación, versión y reversión.
4. **Ciclo completo:** la medición posterior demuestra mejora o activa rollback.

## Fuera de alcance

- Entrenar modelos con información de los empresarios.
- Modificar producción, código o skills sin aprobación humana.
- Publicar automáticamente.
- Copiar memoria de diferentes empresas a un repositorio central.
- Reactivar el auto-patch directo descrito en E24.

---

# Gates entre épicas

| Gate | Pregunta que debe responderse | Si falla |
|---|---|---|
| E42 → E43 | ¿Tenemos una línea base real de claridad, evidencia y utilidad? | No construir la capa agentic; corregir primero el producto actual. |
| E43 → E44 | ¿Las recomendaciones ya son trazables y suficientemente confiables? | Fortalecer revisión y evidencia antes de aprender de ellas. |
| E44 → E45 | ¿Existe suficiente historial de decisiones y resultados? | Mantener un solo coach y seguir reuniendo resultados. |
| E45 → E46 | ¿Los especialistas mejoran casos complejos de forma medible? | Reducir roles o cancelar la colaboración innecesaria. |
| E46 → release | ¿La mejora pasó pruebas, aprobación y puede revertirse? | Mantenerla como propuesta; no promoverla. |

# Métricas comunes del programa

## Confianza

- Recomendaciones con fuentes visibles.
- Contradicciones detectadas antes de responder.
- Cálculos que pueden reproducirse.
- Incertidumbres declaradas.

## Utilidad empresarial

- Tiempo hasta una acción clara.
- Decisiones tomadas.
- Acciones con responsable y fecha.
- Resultados revisados.
- Calificación de claridad y utilidad por empresarios.

## Simplicidad

- Preguntas sencillas resueltas sin equipo multi-agente.
- Respuestas ejecutivas que pueden leerse en menos de cinco minutos.
- Número de conceptos internos o técnicos mostrados al empresario: cero salvo
  que los solicite.

## Seguridad

- Cero envíos automáticos de datos empresariales.
- Cero cambios automáticos de skills o código.
- Cero inferencias psicológicas desde reuniones.
- Cien por ciento de mejoras aprobadas, versionadas y reversibles.

# Riesgos del programa

| Riesgo | Impacto | Mitigación |
|---|---:|---|
| Teatro multi-agente: más actividad sin mejor respuesta | Alto | Comparar contra línea base y cancelar roles que no agreguen valor. |
| Multiplicar errores porque varios agentes repiten el mismo supuesto | Alto | Crítico y verificador deben usar evidencia independiente. |
| Aprender causalidades falsas | Alto | Separar resultado observado, interpretación y causalidad confirmada. |
| Exponer información de personas o empresas | Alto | Local-only, redacción, consentimiento y exportación explícita. |
| Sobreajustar ESCALA a una sola empresa o clase | Medio | Exigir patrones repetidos y casos de distintas decisiones. |
| Volver lenta una conversación sencilla | Medio | Router simple/complex y límites de trabajo. |
| Abrir demasiadas épicas sin terminar la validación actual | Alto | Inicializar una épica a la vez; las demás permanecen como roadmap. |

# Decisión recomendada

Continuar con E42 y capturar la línea base. Si E42 demuestra que el producto
actual puede instalarse, completar un caso y explicar claramente sus límites,
abrir E43. No iniciar E44-E46 antes de demostrar el gate anterior.
