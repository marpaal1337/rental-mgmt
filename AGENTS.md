# rental-mgmt — Conocimiento acumulado del proyecto

## Identidad

Soy el asistente de desarrollo de **rental-mgmt**, un sistema de gestión inmobiliaria
single-user para España. Mi función es implementar las fases del plan, mantener la
calidad del código, y **mantener actualizada la documentación**.

## Estado actual

- **Fase completada**: Fase 10 — Calidad (backups, cobertura, soft-delete audit)
- **Próxima fase**: — (plan completado)
- **Plan director**: `rental-mgmt-plan.md`
- **Stack**: Python 3.11+, FastAPI, SQLModel, SQLite (WAL), Alembic, reportlab, pytest, ruff
- **Frontend**: Vite + React 19 + TypeScript + Ant Design + React Router + Axios
- **E2E**: Playwright (chromium)

## Documentación del proyecto

| Archivo | Propósito | ¿Auto-generable? |
|---|---|---|
| `DOCUMENTO_FUNCIONAL.md` | Visión usuario/negocio: entidades, servicios, casos de uso | No (narrativa) |
| `DOCUMENTO_TECNICO.md` | Documentación técnica: modelos, servicios, tests, DB, convenios | Sí (vía `scripts/generate_docs.py`) |

## Instrucciones obligatorias

### 1. Mantener la documentación actualizada

Siempre que se complete una fase o se haga un cambio relevante en el proyecto,
**debo actualizar ambos documentos** (`DOCUMENTO_FUNCIONAL.md` y
`DOCUMENTO_TECNICO.md`) para reflejar el nuevo estado. Esto incluye:

- Nuevos modelos/entidades añadidos
- Nuevos servicios creados
- Nuevos endpoints de API
- Nuevos tests
- Cambios en el stack o configuración
- Cambios en la estructura del proyecto

### 2. Secuencia de actualización

Al completar una fase:
1. Actualizar `DOCUMENTO_FUNCIONAL.md` con las nuevas capacidades
2. Ejecutar `python scripts/generate_docs.py` para regenerar `DOCUMENTO_TECNICO.md`
3. Verificar que ambos documentos reflejan correctamente el estado actual
4. Actualizar la sección "Estado actual" de este mismo archivo (AGENTS.md)

### 3. Conocimiento acumulado

Este archivo contiene el conocimiento acumulado del proyecto. Cuando se
complete una fase, debo actualizar:

- La sección "Estado actual" con la fase completada y la siguiente
- Cualquier convenio o regla que haya surgido durante la implementación
- Cualquier decisión arquitectónica relevante

## Convenios del proyecto

- **Lógica en services/**: toda la lógica de negocio va en `app/services/`, nunca en modelos ni routers
- **Routers finos**: los endpoints FastAPI solo llaman a servicios y serializan respuestas
- **Decimal para dinero**: usar `Decimal`, nunca `float` para importes
- **Soft-delete**: `deleted_at IS NULL` para registros activos. Nunca borrar datos contables
- **Migraciones**: toda creación/modificación de esquema vía Alembic, nunca `create_all`
- **Transacciones**: los servicios reciben `session` externamente (injection)
- **Tests**: usar SQLite in-memory via fixtures, sesión limpia por test
- **Alembic migrations**: añadir `import sqlmodel` manualmente al generarlas (limitación de SQLModel)

## Estructura del proyecto

```
rental-mgmt/
├── app/
│   ├── models/        → SQLModel entities
│   ├── services/      → Lógica de negocio
│   ├── api/           → Routers FastAPI
│   │   └── routers/   → leases, invoices, payments, expenses,
│   │                   owners, tenants, properties, units,
│   │                   reconciliation, stats
│   └── jobs/          → APScheduler jobs
├── frontend/
│   ├── src/
│   │   ├── api/       → Axios client + endpoints
│   │   ├── pages/     → Dashboard, Leases, Invoices, Payments, Expenses
│   │   ├── components/→ AppLayout, LeaseForm, PaymentForm, ExpenseForm
│   │   └── types/     → TypeScript interfaces
│   └── e2e/           → Playwright E2E tests
├── data/
│   ├── db/            → SQLite database (ignorada por git)
│   ├── backups/       → Backup automáticos (Fase 10)
│   └── invoices/      → PDFs generados
├── tests/             → Pytest tests
├── alembic/           → Migraciones
├── scripts/           → Scripts auxiliares (doc generation, etc.)
├── DOCUMENTO_FUNCIONAL.md
├── DOCUMENTO_TECNICO.md
└── AGENTS.md          ← Este archivo
```

## Skills externas instaladas

| Skill | Propósito | Repo |
|---|---|---|
| `frontend-design` | Interfaces frontend distintivas evitando estética AI genérica | anthropics/skills |
| `vercel-react-best-practices` | 70+ reglas de optimización React/Next.js | vercel-labs/agent-skills |
| `web-design-guidelines` | Auditoría de UI contra estándares de accesibilidad y UX | vercel-labs/agent-skills |

## Fases del plan

1. ✅ **Fase 0** — Bootstrap (FastAPI hello, pytest, ruff, estructura)
2. ✅ **Fase 1** — Modelo core (Owner, Property, Unit, Tenant, Lease, RentCondition, TaxProfile, Deposit)
3. ✅ **Fase 2** — LeaseService + IndexUpdateService (renta vigente, revisiones IPC)
4. ✅ **Fase 3** — Facturación (Invoice, InvoiceLine, InvoiceService)
5. ✅ **Fase 4** — PDF de factura
6. ✅ **Fase 5** — Pagos
7. ✅ **Fase 6** — Gastos
8. ✅ **Fase 7** — Conciliación bancaria
9. ✅ **Fase 8** — API REST completa
10. ✅ **Fase 9** — Automatización (APScheduler)
11. ✅ **Fase 10** — Calidad (backups, cobertura, soft-delete audit)
