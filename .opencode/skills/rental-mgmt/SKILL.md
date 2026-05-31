---
name: rental-mgmt
description: Use when working on the rental-mgmt project (rental management system for Spain). Covers models, services, migrations, conventions, and doc update workflow. Use ONLY for rental-mgmt code changes.
---

# rental-mgmt — Skill de proyecto

Sistema de gestión inmobiliaria single-user para España.

## Stack

Python 3.11+ | FastAPI | SQLModel | SQLite (WAL) | Alembic | pytest | ruff

## Estructura

```
app/models/      → SQLModel entities (AuditMixin + modelos de dominio)
app/services/    → Lógica de negocio (LeaseService, IndexUpdateService)
app/api/         → Routers FastAPI (vacío, Fase 8)
app/jobs/        → APScheduler (vacío, Fase 9)
tests/           → Pytest (conftest.py con fixtures in-memory)
alembic/         → Migraciones
scripts/         → generate_docs.py
```

## Modelos actuales (9 tablas)

1. `owner` — Propietario (FK en property y lease)
2. `property` — Inmueble (FK: owner)
3. `unit` — Unidad alquilable (FK: property)
4. `tenant` — Inquilino (FK en lease)
5. `lease` — Contrato central (FK: unit, tenant, owner)
6. `rent_condition` — Histórico de rentas (FK: lease)
7. `tax_profile` — Perfil fiscal 1:1 con lease (FK: lease, UNIQUE)
8. `deposit` — Fianza 1:1 con lease (FK: lease, UNIQUE)
9. `index_update` — Revisiones IPC/IRAV (FK: lease)

## Servicios actuales

- `LeaseService.get_active_rent(session, lease_id, date?) → Decimal`
- `IndexUpdateService.apply_index(session, lease_id, index_rate, date, ...) → tuple`

## Convenios

- Lógica **siempre** en services/, nunca en modelos ni routers
- Decimal para dinero, nunca float
- Soft-delete con `deleted_at IS NULL`
- Migraciones vía Alembic (nunca create_all)
- Sesión inyectada externamente en servicios
- Tests con SQLite in-memory, sesión limpia por test
- Al generar migraciones, añadir `import sqlmodel` (limitación de SQLModel)

## Flujo de actualización de documentación

Al completar cada fase:
1. Actualizar `DOCUMENTO_FUNCIONAL.md` (narrativa de negocio)
2. Ejecutar `python scripts/generate_docs.py` (regenera `DOCUMENTO_TECNICO.md`)
3. Actualizar sección "Estado actual" en `AGENTS.md`
