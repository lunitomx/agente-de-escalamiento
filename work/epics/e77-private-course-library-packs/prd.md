---
epic_id: E77
title: PRD — Biblioteca privada de cursos y packs instalables
status: planned
---

# PRD E77

## Usuario y trabajo a resolver

Una persona empresaria toma cursos, acumula notas y obtiene ideas valiosas,
pero esas ideas se pierden entre chats, PDFs y recuerdos. Quiere aplicar lo
aprendido a su empresa sin tener que volver a explicar el curso, exponer
material privado ni navegar un catálogo de herramientas técnicas.

## Experiencia objetivo

La persona entrega a ESCALA un curso que tiene derecho a usar. ESCALA explica
qué entendió, qué es aplicable, qué falta comprobar y ayuda a usar una idea
concreta para tomar una decisión o ejecutar un experimento. La experiencia
sigue siendo una conversación única; los packs son internos.

## Flujo

1. La persona selecciona una fuente local y confirma uso/retención.
2. ESCALA crea un inventario y presenta candidatos, huecos y referencias.
3. La persona revisa qué puede usarse localmente.
4. Sólo los candidatos aprobados se compilan a ejercicios/procedimientos.
5. Cuando una necesidad empresarial coincide, ESCALA propone el ejercicio,
   explica qué datos necesita y pide confirmación antes de guardar resultados.
6. La salida se convierte en un artefacto, decisión, acción o experimento
   revisable; nunca en un hecho automático de la empresa.

## Requisitos funcionales

- Alta, inspección, versión, pausa, actualización y retiro de packs privados.
- Búsqueda por intención y procedencia; activación/no-activación explicables.
- Manifest local con hash, tipo de fuente, calidad y permisos.
- Conjunto de candidatos, relaciones, conflictos, referencias y revisión.
- Procedimientos compilados bajo el contrato E65.
- Estado de empresa separado de contenido de curso.
- Resultados de evaluación que detecten contenido sin fuente, inferencia
  excesiva, fuga de datos, duplicación de capacidades y routing incorrecto.

## Requisitos no funcionales

- Local-first: sin telemetría ni carga automática de archivos.
- Private-by-default: contenido y derivado restrictivo no entran al repositorio
  ni export público.
- Portable: el core no depende de Claude o Codex; adaptadores se aíslan en E67.
- Revocable: retirar un pack no borra documentos empresariales aprobados, pero
  elimina su capacidad de activación y conserva procedencia de los artefactos.
- Accesible: lenguaje de negocio, no nombres de archivos, modelos ni skills.

## Métricas de piloto

- Tiempo de fuente a primer ejercicio revisable.
- Porcentaje de candidatos con procedencia completa.
- Precisión de activación y no-activación.
- Número de afirmaciones bloqueadas/corregidas antes de promoción.
- Claridad reportada por el empresario sobre el siguiente paso.
- Cero contenido crudo o datos de empresa fuera de la instalación privada.

## Decisiones de producto

- Los cursos son extensiones privadas, no parte del agente base.
- BlackSeller es el primer caso de prueba; no se distribuye con ESCALA.
- E71 conserva investigación de mercado; E69 conserva la biblioteca de la
  metodología base. E77 sólo añade una fuente privada y controlada.
