# Escala Server

Servidor HTTP local para coaching empresarial con dashboards interactivos, persistencia SQLite, memoria neurosimbólica y ciclo de sesiones.

## Instalación

```bash
# 1. Clonar el proyecto
git clone <repo-url> && cd ScaliingUPAI

# 2. Iniciar el servidor
python3 -m escala_server

# 3. Abrir en el navegador
open http://localhost:8080
```

## CLI Reference

| Comando | Descripción |
|---------|-------------|
| `python3 -m escala_server` | Inicia servidor en puerto 8080 |
| `python3 -m escala_server --port 9090` | Puerto personalizado |
| `python3 -m escala_server --db-path ~/mi-base.db` | Base de datos personalizada |
| `python3 -m escala_server.cli status` | Ver estado del servidor |
| `python3 -m escala_server.cli stop` | Detener servidor |
| `python3 -m escala_server.cli migrate` | Migrar datos YAML → SQLite |
| `python3 -m escala_server.cli inicia` | Iniciar sesión de coaching |
| `python3 -m escala_server.cli cierra` | Cerrar sesión de coaching |

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Home page con 4 tarjetas de decisión |
| GET | `/api/health` | Health check |
| GET | `/api/companies` | Listar empresas |
| POST | `/api/companies` | Crear empresa |
| GET/POST | `/api/worksheets/{category}/{tool}` | Leer/guardar worksheet |
| GET/POST | `/api/sessions` | Listar/crear sesiones |
| GET/POST | `/api/memory/facts` | Listar/crear hechos |
| GET | `/api/memory/context` | Contexto relevante para sesión |
| POST | `/api/memory/entities` | Crear entidad |
| POST | `/api/memory/relationships` | Crear relación |
| GET | `/api/memory/graph/{id}` | Grafo de entidad |

## Arquitectura

```
escala_server/
├── __init__.py          # Versión del paquete
├── __main__.py          # Entry point del servidor
├── server.py            # HTTP server + rutas API
├── handlers.py          # API handlers (companies, worksheets, sessions, memory)
├── router.py            # URL dispatcher con path params
├── cors.py              # CORS middleware
├── cli.py               # CLI: start, stop, status, migrate, inicia, cierra
├── schema.py            # SQLite schema DDL
├── diff.py              # Diff engine para worksheets
├── migrate.py           # Migración YAML → SQLite
├── memory_engine.py     # Memoria neurosimbólica con trust scores
├── graph_engine.py      # Grafo entidad-relación con BFS traversal
├── daos/                # SQLite DAOs por dominio
│   ├── base.py          # BaseDAO con conexión compartida
│   ├── company_dao.py   # CRUD empresas
│   ├── worksheet_dao.py # Worksheets versionados
│   ├── session_dao.py   # Sesiones
│   └── change_dao.py    # Change tracking
├── session/             # Orquestadores de sesión
│   ├── session_start.py # escala-inicia
│   └── session_close.py # escala-cierra
└── static/              # Frontend
    ├── index.html       # Home page
    ├── shared/          # CSS/JS/vendor compartido
    └── dashboards/      # 22 dashboards por decisión
        ├── cash/        # 5 dashboards
        ├── strategy/    # 5 dashboards
        ├── people/      # 6 dashboards
        └── execution/   # 7 dashboards
```
