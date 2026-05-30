# Rental Management System

Sistema de gestión inmobiliaria para single-user en España.

## Instalación

```bash
# En terminal Windows (PowerShell o CMD)
python -m pip install -e ".[dev]"
```

## Configuración

```bash
# Copiar archivo de entorno
copy .env.example .env

# Editar .env si necesitas cambiar valores predeterminados
```

## Ejecución

```bash
# Iniciar servidor
uvicorn app.main:app --reload

# Ejecutar tests
pytest

# Linting
ruff check .
```

## Estructura del proyecto

```
rental-mgmt/
├── app/
│   ├── models/        # SQLModel entities
│   ├── services/      # Lógica de negocio
│   ├── api/           # Routers FastAPI
│   └── jobs/          # APScheduler jobs
├── data/
│   ├── db/            # SQLite database
│   └── invoices/      # PDFs generados
├── templates/         # Jinja2 templates
├── tests/
└── alembic/           # Migraciones
```
