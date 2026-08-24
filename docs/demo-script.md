# Guion de demo — ScaleUp

**Duración objetivo:** 60–90 minutos.
**Audiencia:** dueños o líderes de empresa sin experiencia previa con IA,
Scaling Up, comandos o archivos de proyecto.

## Preparación (5–10 min)

Usa una carpeta nueva para no mezclar datos reales. Instala el canal que se
vaya a mostrar:

```bash
bash .scaleup/install.sh --target claude
# o
bash .scaleup/install.sh --target codex
```

Comprueba la instalación con `bash .scaleup/install.sh --target <canal> --status`.
Abre Claude Code o Codex en la carpeta de demo. No escribas slash commands.

Al terminar una demo local, puedes retirar ScaleUp de todos los canales sin
borrar el runtime de la demo con:

```bash
bash .scaleup/install.sh --uninstall
```

No uses `--purge` durante una demo: elimina el runtime instalado, pero no los
artefactos que el asistente haya guardado en la carpeta de proyecto. Para
limpiar por completo una demo, abre su carpeta exacta, revisa `.scaleup/` y
`work/strategy/opsp.md`, y elimínalos manualmente. No borres esos directorios
desde una carpeta que contenga otros proyectos.

### Empresa ficticia

**Lumen Casa** vende iluminación decorativa por internet y a distribuidores en
México. Tiene 28 personas. Creció rápido, pero sus entregas son variables, el
equipo no tiene prioridades comunes y el efectivo se tensa por inventario. Su
ambición es ser la marca de iluminación de diseño más confiable para hogares y
pequeños hoteles en México.

## Recorrido

| Tiempo | Prompt que se escribe | Respuesta o checkpoint esperado |
|---|---|---|
| 0–5 min | `Quiero organizar mi empresa; no sé por dónde empezar.` | El coach inicia sin pedir comandos, explica brevemente el proceso y pregunta nombre y actividad. |
| 5–15 min | `Se llama Lumen Casa. Vendemos iluminación decorativa en línea y a distribuidores en México. Somos 28 personas.` | Completa el perfil con una pregunta a la vez; confirma el resumen antes de continuar. **Artefacto:** perfil persistido bajo `.scaleup/`. |
| 15–30 min | Responde las preguntas con: `Personas: 2; estrategia: 3; ejecución: 2; efectivo: 1. El inventario nos deja sin efectivo.` | Realiza o completa el diagnóstico de las cuatro decisiones y explica en lenguaje simple por qué Efectivo es el foco inicial. **Checkpoint:** diagnóstico y prioridad guardados. |
| 30–45 min | `Ahora quiero hacer mi plan estratégico en una hoja.` | El coach reconoce la intención, explica “plan en una hoja” sin depender de la sigla OPSP, y comienza con valores. |
| 45–65 min | `Nos importan diseño honesto, cumplir lo prometido, resolver rápido y cuidar al cliente.` | Pide propósito, meta ambiciosa, mercado, promesa, metas y prioridades una por una. Datos sugeridos: propósito “hacer que los espacios cotidianos se sientan extraordinarios”; meta a 10 años “ser la marca mexicana de iluminación más confiable”; promesa “entrega completa en 72 horas para productos disponibles”; métrica trimestral “pedidos completos entregados a tiempo”; prioridad “reducir faltantes de inventario”. |
| 65–75 min | `Sí, guárdalo y dime qué haríamos primero este trimestre.` | Resume decisiones, asigna un siguiente paso concreto y guarda el plan. **Artefacto obligatorio:** `work/strategy/opsp.md` con valores, propósito, meta, mercado, promesa, metas y prioridades. |
| 75–85 min | Cierra y vuelve a abrir el asistente. Escribe: `¿Cómo vamos y qué sigue?` | Recupera el contexto sin volver a pedir toda la información y muestra el siguiente paso. **Checkpoint:** continuidad demostrada. |

## Recuperación durante la demo

- Si falta un dato, responde “todavía no lo sé”. El coach debe proponer un
  borrador, explicar que se puede ajustar y continuar con una pregunta.
- Si el asistente pide un comando o muestra un nombre de skill, vuelve a escribir
  la intención completa en lenguaje natural. Registra el fallo: es una brecha
  del release, no un error del presentador.
- Si no aparece el plan guardado, muestra el perfil y el diagnóstico ya
  persistidos; explica que la generación/persistencia del OPSP es la parte que
  requiere corrección antes del release.
- Si un canal falla, no simules equivalencia. Continúa sólo con el canal que
  tenga evidencia y marca el otro como pendiente en `docs/demo-readiness.md`.

## Limitaciones que se deben declarar

- ScaleUp es guía metodológica, no asesoría financiera, fiscal ni legal.
- La conversación y los artefactos se guardan localmente; no uses datos reales
  sensibles en una demo compartida.
- La desinstalación no rastrea los proyectos donde se guardaron artefactos. La
  limpieza de esos proyectos es manual hasta que el producto los gestione.
- La aceptación del release exige demostrar el mismo recorrido natural en
  Claude Code y Codex desde estado limpio. Hasta contar con esa evidencia, no
  se debe afirmar paridad sólo porque el instalador copie archivos.
