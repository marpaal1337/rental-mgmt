# Rental Management System

Sistema de gestión inmobiliaria para single-user en España.

## Instalación (desarrollo)

```bash
python -m pip install -e ".[dev]"
cp .env.example .env
```

## Ejecución

```bash
# Escritorio (pywebview, arranca migraciones y servidor)
python -m desktop

# Solo API (desarrollo)
uvicorn app.main:app --reload

# Tests (cobertura mínima 80% en app/services)
pytest

# Linting
ruff check .
```

La API vive bajo `/api` (ej. `/api/leases`). La raíz `/` sirve el frontend.
La autenticación es una API key estática (`X-API-Key`, variable `API_KEY`).

### Datos de demo

En una instalación nueva la base de datos arranca vacía. Para cargar datos de
ejemplo (propietarios, inmuebles, contratos):

```bash
RENTAL_MGMT_DEMO=1 python -m desktop
```

## Empaquetado Windows

```bash
python scripts/build_windows_installer.py             # .exe InnoSetup + .zip
python scripts/build_windows_installer.py --innosetup # solo .exe
python scripts/build_windows_installer.py --zip       # solo .zip portable
```

El pipeline genera el icono, compila el frontend, empaqueta con PyInstaller
(onedir autocontenido, no requiere Python en el equipo destino) y construye el
instalador con InnoSetup. Los datos (`data/db`, `data/backups`,
`data/invoices`) no se eliminan al desinstalar.

## Estructura del proyecto

```
rental-mgmt/
├── app/
│   ├── models/        # SQLModel entities
│   ├── services/      # Lógica de negocio
│   ├── api/           # Routers FastAPI
│   └── jobs/          # APScheduler jobs
├── frontend/          # SPA Vite + React + Ant Design
├── data/
│   ├── db/            # SQLite database (WAL)
│   ├── backups/       # Backups automáticos
│   └── invoices/      # PDFs generados
├── tests/
├── alembic/           # Migraciones
├── build/             # Configuración InnoSetup
└── scripts/           # Build, seed, docs, icono
```
