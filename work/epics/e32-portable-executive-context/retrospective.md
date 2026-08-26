# Retrospectiva: E32 — Contexto Ejecutivo Portátil

**Cierre:** 2026-08-26
**Resultado:** Complete

## Qué cambió

- `AttachmentEnvelope` recibe sólo un adjunto temporal que el host ya autorizó;
  la conversación pide adjuntar, nunca una ruta o JSON al empresario.
- La evidencia confirmada se exporta de forma explícita a una contribución YAML
  mínima. El adjunto, sus bytes, su ruta y SQLite quedan fuera de la carpeta
  compartida.
- E26 sólo reconstruye paneles desde `areas/{decisión}/evidence.yaml` ya
  reconciliado. La contribución append-only conserva el historial; una segunda
  máquina converge de forma idempotente en su propio SQLite.
- `CompanyContext` reúne hechos confirmados, procedencia, fecha y huecos para
  Business Pulse y Board. El Board solicita exclusivamente la proyección
  humana `board`, que registra su acceso y no incluye Accountability privado.

## Evidencia de cierre

- Suite completa: `uv run --with pytest --with pyyaml pytest` — 601 casos,
  con 2 skips existentes.
- Regresión focalizada: adjunto host, privacidad, reconciliación/rebuild entre
  dos máquinas y Board en `tests/test_e32_portable_context.py`.
- Instalador limpio validado por la suite existente y actualizado para incluir
  `company_context.py`.
- RaiSE: `gate-tests` verde; `gate-governance-artifacts` verde. Drift sin
  clones; la advertencia histórica de acoplamiento en router queda registrada
  como señal, no bloqueo.

## Aprendizaje

Compartir una carpeta no significa compartir una base ni todo el contexto. El
límite útil es: propuesta legible, conciliación humana y reconstrucción local.
Así el equipo conserva una fuente verificable sin convertir el producto en un
sistema técnico o de vigilancia.

## Siguiente

E33 debe centrarse en activación y seguimiento de negocio, no en OAuth propio:
mejorar el recorrido de compartir/reconciliar desde lenguaje natural y medir
si los paneles ayudan a cerrar compromisos semanales.
