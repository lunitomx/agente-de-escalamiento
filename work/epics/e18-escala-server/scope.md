# Epic Scope: E18 — Escala Server & Interactive Dashboards

## Objective

Construir un mini servidor HTTP local (Python, sin dependencias externas) que sirva los 22 dashboards visuales de Escala con datos en vivo desde YAML, más un sistema de navegación jerárquica y al menos un dashboard interactivo con sliders/controles que persistan cambios.

## Background

El proyecto ScaleUp tiene 22 dashboards HTML estáticos construidos en E14-E17 (Cash, Strategy, People, Execution). Son visualmente completos pero usan datos de ejemplo (Acme Corp). El flujo de usuario actual requiere que el agente (Claude Code) guíe al usuario a ingresar datos en worksheets y luego el usuario vea el HTML — no hay conexión entre ambos.

## In Scope

### S18.1 — Server Core
- Servidor HTTP minimalista con `python -m http.server` extendido
- Sistema de rutas API: GET/POST para cada herramienta
- Capa de persistencia: leer/escribir YAML en `.escala/my-company/worksheets/`
- Servir archivos estáticos (HTML, CSS, JS, vendor)
- CORS para desarrollo local
- Comando `escala-server start` para iniciar

### S18.2 — Navigation & Home
- Página principal: 4 tarjetas clickeables (Cash, Strategy, People, Execution)
- Cada tarjeta muestra score actual y color de estado
- Sub-navegación: al hacer clic en una decisión, muestra lista de herramientas disponibles
- Breadcrumbs: Home > Cash > Power of One
- Diseño responsive con dashboard-base.css existente

### S18.3 — Power of One Interactive (PILOT)
- Tomar el HTML existente (`e14-cash-dashboards/components/power-of-one/`)
- Agregar sliders (range input) para cada una de las 7 palancas
- Recalcular impacto en tiempo real al mover sliders
- Botón "Guardar" que hace POST /api/cash/power-of-one
- Endpoint API: GET/POST /api/cash/power-of-one
- Persistencia a `.escala/my-company/worksheets/cash/power-of-one.yaml`

### S18.4 — Cash Suite Interactive
- CASh Board: scoreboard general con edición de scores
- Fundability: editores de métricas financieras
- CCC: sliders para días de cada ciclo (sales, delivery, collection)
- Recurring Revenue: editores de MRR/ARR con proyección

### S18.5 — Strategy Suite Interactive
- BMC Board: canvas de 9 bloques editable
- Core Customer: tarjetas de cliente editables
- Brand Promises: medidores de cumplimiento ajustables
- Diff Activities: matriz competitiva editable
- Sandbox: mapa visual configurable

### S18.6 — People Suite Interactive
- Core Values: tarjetas de valores editables
- FACe: matriz de funciones × personas editable
- Team Growth: radar chart con datos editables
- DISC: composición visual editable
- Love/Loathe: balance board editable
- Hiring Pipeline: proceso de 7 pasos editable

### S18.7 — Execution Suite Interactive
- Rockefeller Habits: scoreboard de 10 hábitos editable
- WWW: task tracker visual interactivo
- Priorities: tablero anual editable
- Balanced KPIs: leading/lagging con traffic lights editables
- Meeting Rhythms: calendario visual configurable
- Influencers: board de relaciones estratégicas editable
- Vision Summary: panel central unificado

### S18.8 — Installation & Server Lifecycle
- Integrar con install.sh existente
- Comando `escala-server` CLI (start, stop, status)
- Health check endpoint
- Documentación de instalación y uso

## Out of Scope
- Base de datos externa (SQLite/PostgreSQL)
- Autenticación multi-usuario
- Despliegue cloud
- Integración con CRMs externos
- Exportación a PDF
- Multi-idioma

## Dependencies
- E14-E17 dashboards existentes (HTML, CSS framework, Chart.js)
- Escala skills existentes (escala-cash-power1, etc.)
- Python 3.8+ (ya es requisito)

## Design Decisions

- **DD1:** Server con http.server nativo — sin Flask/FastAPI ni dependencias externas
- **DD2:** Datos en YAML plano en `.escala/my-company/worksheets/{decision}/{tool}.yaml`
- **DD3:** Cada dashboard HTML se modifica mínimamente — se agrega fetch() para datos + controles
- **DD4:** Los HTMLs deben seguir funcionando sin server (modo estático)
- **DD5:** La navegación es HTML puro + JS, sin framework
- **DD6:** S18.3 (Power of One) es el piloto — se construye primero para validar el patrón

## Stories

| ID | Name | Description | Dependencies |
|----|------|-------------|-------------|
| S18.1 | Server Core | HTTP server, routing, YAML persistence, static serving | Ninguna |
| S18.2 | Navigation & Home | 4-card home, sub-navigation, breadcrumbs | S18.1 |
| S18.3 | Power of One Interactive | Sliders, live calc, save to YAML (PILOT) | S18.1 |
| S18.4 | Cash Suite Interactive | 3 remaining cash dashboards interactivos | S18.1, S18.3 |
| S18.5 | Strategy Suite Interactive | 5 strategy dashboards interactivos | S18.1 |
| S18.6 | People Suite Interactive | 6 people dashboards interactivos | S18.1 |
| S18.7 | Execution Suite Interactive | 7 execution dashboards interactivos | S18.1 |
| S18.8 | Installation & Lifecycle | CLI commands, install script, docs | S18.1, S18.2, S18.3 |

## Status: In Progress

## Done Criteria
- [ ] `escala-server start` funciona y sirve todos los dashboards
- [ ] Power of One con sliders funcionales que persisten a YAML
- [ ] Navegación Home → Decisión → Herramienta funciona
- [ ] Al menos Cash suite completamente interactiva
- [ ] Los 22 dashboards se sirven con datos reales (o placeholder cuando no hay datos)
- [ ] `escala-server stop` detiene el servidor limpiamente
- [ ] Documentación de instalación y uso
