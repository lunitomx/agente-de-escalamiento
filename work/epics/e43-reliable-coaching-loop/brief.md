---
epic_id: "E43"
title: "Reliable Coaching Loop"
status: "planned"
depends_on: ["E42"]
created: "2026-07-23"
---

# E43 — Respuestas confiables antes de recomendar

## Hipótesis

Para un empresario que consulta una decisión importante, un coach que primero
aclara la decisión, usa sus archivos locales y se revisa antes de responder
produce recomendaciones más confiables y más fáciles de ejecutar.

A diferencia de una respuesta convincente pero genérica, ESCALA mostrará qué
vio, qué significa, qué no sabe y cuál es el siguiente paso.

## Métricas de éxito

- **Señal temprana:** en los casos de prueba, toda recomendación importante
  contiene evidencia o una pregunta explícita por la información faltante.
- **Resultado:** empresarios califican mejor claridad, confianza y utilidad que
  la línea base capturada en E42.
- **Guardrail:** una contradicción sembrada en Cash o reuniones se detecta antes
  de presentarse como hecho.

## Tamaño

M — seis historias que forman un solo recorrido completo, primero en Cash y
Weekly, después en las cuatro decisiones.

## Dentro

- Aclarar el objetivo antes de analizar.
- Reunir evidencia local de documentos, sesiones, contexto y tareas.
- Elegir la herramienta adecuada para la evidencia disponible.
- Realizar una revisión crítica antes de recomendar.
- Entregar una respuesta ejecutiva en lenguaje empresarial.
- Probar casos positivos, faltantes y contradictorios.

## No-Gos

- No activar un equipo multi-agente; corresponde a E45.
- No aprender de resultados posteriores; corresponde a E44.
- No cambiar prompts, skills o código según una sola sesión; corresponde a E46.
- No enviar documentos o resultados fuera de la máquina local.
- No convertir la respuesta en un reporte técnico para el empresario.

## Rabbit Holes

- Pedir todos los documentos posibles antes de hacer la primera pregunta útil.
- Mostrar la cadena interna de análisis en vez de una decisión clara.
- Marcar como certeza una inferencia razonable.
- Diseñar una nueva plataforma de agentes en lugar de ampliar los flujos que ya
  existen.
