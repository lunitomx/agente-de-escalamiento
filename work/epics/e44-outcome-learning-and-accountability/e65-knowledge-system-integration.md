# Integración E44 con el programa de conocimiento

E44 conserva la propiedad del ciclo `decisión → acción → resultado → aprendizaje`; no se crea una épica E66 que lo duplique.

## Ajustes de dependencia

- Puede empezar con sus historias S44.1-S44.2 usando contratos de E49/E52.
- S44.3-S44.5 se integran con E65 para que cada procedimiento del MVP escriba decisión, responsable, métrica, cadencia y evidencia con un formato común.
- Las rutas que consuman datos multifuente requieren las historias de hechos y onboarding adaptativo de E55.
- Sólo aprendizajes confirmados pasan a memoria reutilizable; `fact`, `hypothesis`, `assumption`, `decision` y `commitment` no se mezclan.

## Cierre adicional

El estado de empresa, líder y trimestre debe poder reconstruir qué se decidió, con qué evidencia, quién aceptó el aprendizaje y cuándo debe revisarse. El histórico es append-only; una corrección crea una versión, no sobrescribe el pasado aprobado.
