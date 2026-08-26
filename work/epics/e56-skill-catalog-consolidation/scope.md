# Alcance E56 — Un solo orquestador y catálogo canónico

## Dentro del alcance

| Área | Entrega de E56 | Límite |
|---|---|---|
| Inventario | Registro versionado de cada `escala-*`, `scaleup-*` y copia de agente: intención, consumidor, fuente, dueño, destino y disposición Bitter Pill. | El registro describe comportamiento existente; no inventa capacidades. |
| Entrada pública | Un contrato `escala` orientado a conversación que detecta estado, intención y siguiente acción. | Los especialistas pueden seguir existiendo internamente. |
| Fuente única | `escala-skills/` y/o módulos Python definidos por el registro como fuente de verdad; los artefactos de plataforma derivan de ella. | No se mantiene una segunda copia editable a mano. |
| Compatibilidad | Mapa explícito de aliases `scaleup-*` al contrato canónico, con aviso y condición de retiro. | No se promete compatibilidad eterna ni se duplican implementaciones. |
| Distribución | Instalador y pruebas que comprueban exactamente qué recibe Claude, Codex y Hermes. | E56 no añade conectores de terceros. |
| Experiencia | Guía y casos de aceptación para empresarios que nunca han usado un agente. | No es un rediseño visual del cockpit. |

## Fuera del alcance

- Conciliar Excel, conversación y datos de negocio: E55.
- Persistencia semántica y consentimiento entre sesiones: E52 y sus extensiones.
- Crear nuevas metodologías de Scaling Up, dashboards, paneles o especialistas.
- Enviar información fuera de la carpeta local o cambiar la política de
  privacidad/evidencia vigente.
- Borrar archivos de usuario, workspaces o historiales durante la migración.

## Invariantes de producto

1. **Una puerta para el empresario.** La interfaz pública empieza por `escala`
   y lenguaje natural; la taxonomía interna no es una tarea del usuario.
2. **Verdad y trazabilidad.** Cualquier diagnóstico conserva evidencia,
   procedencia, frescura, incertidumbre y consentimiento como ya exige E49/E55.
3. **Local primero.** La consolidación no convierte una carpeta compartida ni
   un conector en autoridad automática.
4. **Compatibilidad segura.** Un nombre legado sólo puede redirigir, advertir o
   fallar de manera explicable; jamás ejecutar lógica distinta de forma oculta.
5. **Sin pérdida por refactor.** Ninguna disposición `retired` se ejecuta hasta
   que su reemplazo, prueba de regresión, migración y recibo de decisión existan.

## Criterios de aceptación de épica

- El catálogo auditado cubre 62 `escala-*`, 39 `scaleup-*` y cada directorio
  espejo descubierto en el commit de inicio, con una decisión verificable por
  entrada.
- El flujo de instalación limpio expone la entrada pública prevista y verifica
  que no haya nombres técnicos/huérfanos fuera de la política de distribución.
- Cinco rutas de lenguaje natural (primera conversación, retomar contexto,
  pedir diagnóstico, pedir ayuda y usar alias legado) alcanzan el contrato
  correcto o un límite claro, sin requerir que la persona elija un skill.
- Todo alias legado conservado llega a la misma implementación canónica y tiene
  aviso, propietario y criterio de caducidad; la excepción Rockefeller queda
  decidida explícitamente, no olvidada.
- Una edición de una fuente canónica no puede crear deriva silenciosa en un
  artefacto soportado; las pruebas detectan hashes, manifest o contenido
  contradictorio según el mecanismo seleccionado.
- La documentación de instalación y migración explica, en español sencillo,
  qué se instala, qué conserva el usuario y cómo pedir ayuda.

## Riesgos y mitigaciones

| Riesgo | Mitigación / dueño |
|---|---|
| Confundir copiar nombres con preservar comportamiento | S56.1 exige mapeo de intención, consumidor y caso de regresión antes de disposición. |
| Un router genérico degrade un flujo especializado | S56.2 define contratos y golden cases por familia antes del corte. |
| Instaladores activos dependan de skills individuales | S56.3 hace empaquetado determinista y prueba instalación limpia antes de retirar. |
| Retiro prematuro de `scaleup-*` | S56.4 mantiene adaptadores finitos, telemetría local/recibos y rollback. |
| E56 invada E55 o E52 | La matriz de ownership y los no-gos bloquean cambios metodológicos o de datos. |
