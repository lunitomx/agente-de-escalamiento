# Diseño: E30 — Accountability Empresarial Longitudinal

## Evidencia de partida

La auditoría de siete worksheets EO Accelerator encontró la misma secuencia:

1. actualización personal y de negocio;
2. issue statement;
3. People, Strategy, Execution o Cash y herramienta probada;
4. background, current situation y future options;
5. incertidumbre, contribución propia, impacto del fallo y reto personal;
6. outcome deseado y confianza 0–100;
7. notas/opciones del grupo.

E24 registra compromisos semanales, pero no representa una sesión de grupo ni
su worksheet. E22 puede guardar patrones confirmados, pero no calcula patrones
de Accountability. FACe cubre funciones internas, no este proceso.

## Modelo

- `accountability_sessions`: worksheet, fuente, fecha, consentimiento y estado.
- `accountability_commitments`: Who/What/When, medida de éxito y revisión.
- `accountability_exclusions`: exclusión reversible del análisis.

La revisión deriva un porcentaje transparente desde cuatro criterios explícitos:
resultado, evidencia, plazo y aprendizaje. La fuente de verdad sigue siendo el
estado narrativo y su evidencia; el porcentaje sólo resume la rúbrica.

## Patrones permitidos

- distribución por decisión;
- cumplimiento de compromisos;
- bloqueos repetidos con texto normalizado;
- confianza alta seguida de resultados incompletos;
- temas que aparecen en dos o más sesiones mediante etiquetas confirmadas.

Cada patrón devuelve los IDs/fechas de las sesiones que lo sustentan. Una sola
aparición se etiqueta observación, no patrón.

## Privacidad

La previsualización detecta marcadores de datos personales, legales, salud,
credenciales y cifras financieras. No guarda el texto hasta recibir confirmación
explícita. La actualización personal nunca alimenta inferencias psicológicas.
