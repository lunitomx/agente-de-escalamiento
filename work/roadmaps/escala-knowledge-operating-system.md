# Programa: sistema operativo de conocimiento de ESCALA

**Estado:** planificado el 2026-08-26
**Puerta pública:** `escala` — una conversación natural; ninguna colección de comandos para el empresario.
**Fuente de metodología:** privada, con trazabilidad y prohibida por defecto en cualquier exportación.

## Decisión

El producto no será un buscador conversacional sobre un libro ni una colección de formularios. Será un ciclo verificable:

```text
fuente privada autorizada
  → manifiesto y candidatos auditables
  → ontología canónica con evidencia
  → procedimientos internos versionados
  → orquestador único `escala`
  → artefacto + responsable + métrica + cadencia
  → estado local consentido + revisión
  → evaluación y aprendizaje confirmado
```

La ontología existente en `conocimiento/` se evoluciona; no se crea un segundo grafo. SQLite puede ser un índice/caché derivado, nunca la autoridad ni un archivo compartido. La memoria de empresa y líder permanece local; una carpeta sincronizada sólo puede intercambiar archivos de entrada/salida, no la base SQLite.

## Hechos de partida

| Activo existente | Decisión de este programa |
|---|---|
| E1901 parser/grafo | No declararlo completo: sólo inventario parcial; se reemplaza su estándar de cobertura. |
| E6 ontología YAML y retrieval | Migrarla con compatibilidad; no duplicarla. |
| E30/E31 pipelines | Reusar su runner; no construir otro motor de workflows. |
| E35 golden cases | Ampliarlo a fidelidad semántica y cross-platform. |
| E49/E55 diagnóstico y evidencia | Son los consumidores de hechos y ruta de 90 días; E55 sigue en curso. |
| E52 memoria consentida y E44 seguimiento | Se integran y amplían; E44 conserva la propiedad del loop de resultados. |
| E56 catálogo | Se conserva: `escala` es la única entrada instalada; capacidades son internas. |

## Frontera de derechos y publicación

El corpus actual declara restricciones editoriales. E36 impide exportar el archivo crudo, pero no acredita derechos de redistribución ni de derivados. Por ello E57 debe negar tanto corpus como derivados hasta una disposición explícita de derechos. El trabajo privado puede avanzar; la publicación comercial queda bloqueada por E70 hasta revisión humana/profesional. Esto es una condición de producto, no una conclusión legal.

## Ruta crítica

```text
E57 → E58 → ┬ E59 (fundamentos)
             ├ E60 (People)
             ├ E61 (Strategy)
             ├ E62 (Execution)
             └ E63 (Cash)
                    ↓
                   E64 → E65 → E67 → E68 → E69 → E70
                                  ↘ E44 ampliada ↗

E55 continúa en paralelo y es requisito de las rutas que usen evidencia multifuente.
```

## Orden de valor

El primer release de capacidad no espera toda la biblioteca. E65 compila un MVP de seis intervenciones: diagnóstico, OPPP de líder, resumen de visión, prioridad trimestral, ritmo de reuniones y revisión trimestral. E68 exige un piloto trimestral antes de abrir E69, donde se incorpora el resto por olas.

## Métricas y gates globales

- Todas las unidades estructurales del corpus quedan clasificadas o excluidas con motivo.
- Toda regla, cifra, fórmula o prescripción lleva evidencia de fuente.
- Un extractor nunca aprueba su propia extracción.
- Ninguna pregunta/artefacto puede completar datos empresariales inventados.
- Ningún procedimiento se promueve sin trigger, non-trigger, salida, criterios de aceptación, actualización de estado y pruebas.
- El instalador expone sólo `escala`; Codex y Claude se comparan por resultado semántico, no por redacción idéntica.
- Sólo aprendizajes confirmados por el empresario se reutilizan; observación, hipótesis y causalidad permanecen separadas.

## No objetivos

- No crear RAG/vector DB como fuente de verdad.
- No alojar datos, sincronizar SQLite ni incorporar OAuth/conectores de Drive.
- No construir una metodología completa de autores externos que sólo aparezcan citados en el corpus.
- No llamar "terminado" al sistema por una demo o por tests sintéticos.
