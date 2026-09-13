# rental-mgmt — Conocimiento acumulado del proyecto

## Identidad

Soy el asistente de desarrollo de **rental-mgmt**, un sistema de gestión inmobiliaria
single-user para España. Mi función es implementar las fases del plan, mantener la
calidad del código, y **mantener actualizada la documentación**.

## Estado actual

- **Fase completada**: Fase 12.2 — Informes fiscales (303 IVA trimestral, 190 retenciones, 100 rendimiento por propiedad) + IVA opcional en gastos
- **Próxima fase**: Fase 12.3 — Avisos de impago y actividad; después 12.4 plazos de fianza
- **Plan director**: `rental-mgmt-plan.md`
- **Stack**: Python 3.11+, FastAPI, SQLModel, SQLite (WAL + FK), Alembic, reportlab, pytest, ruff
- **Frontend**: Vite + React 19 + TypeScript (strict) + Ant Design + React Router + Axios + TanStack Query
- **E2E**: Playwright (chromium), 10 tests
- **Tests**: 202 tests, cobertura mínima 80 % en `app/services` (actual ~97 %)
- **CI**: GitHub Actions (`.github/workflows/ci.yml`): ruff + pytest + lint/build frontend + E2E
- **Empaquetado**: PyInstaller onedir + InnoSetup (vía única)

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

## Windows installer

Vía única de empaquetado: **PyInstaller (onedir autocontenido) + InnoSetup**.
El equipo destino no necesita Python. El spec `rental-mgmt.spec` incluye
`collect_submodules("app")`, `frontend/dist`, `alembic`, `alembic.ini` e
`build/icon.ico`.

| Paso | Herramienta | Resultado |
|---|---|---|
| 1 | `scripts/generate_icon.py` | `build/icon.ico` |
| 2 | `npm run build` | `frontend/dist/` |
| 3 | PyInstaller | `dist/rental-mgmt/` (exe + `_internal/`) |
| 4 | InnoSetup | `dist/rental-mgmt-setup-*.exe` |

Script unificado: `scripts/build_windows_installer.py`
```
python scripts/build_windows_installer.py             # .exe + .zip
python scripts/build_windows_installer.py --innosetup # Solo .exe
python scripts/build_windows_installer.py --zip       # Solo .zip portable
python scripts/build_windows_installer.py --skip-frontend
```

`frontend/dist` está ignorado por git y se reconstruye siempre al empaquetar.
InnoSetup empaqueta el contenido de `dist/rental-mgmt/` (no fuentes).

### desktop.py — flujo de arranque

```
desktop.py
  ├── backup_if_exists()        → backup SQLite (integrity_check) → data/backups/pre-upgrade-*.db
  ├── run_migrations()          → alembic upgrade head (aborta con diálogo si falla)
  ├── seed_demo_if_enabled()    → solo si RENTAL_MGMT_DEMO=1 y Owner vacío
  ├── catch_up_jobs()           → facturación del mes en curso + detección de impagos
  ├── uvicorn (127.0.0.1, log_level=error, sin access_log)
  ├── poll a /health (timeout 15s) antes de abrir ventana
  └── pywebview con icon.ico o navegador
```

### Icono de app

| Archivo | Propósito |
|---|---|
| `frontend/public/favicon.svg` | Icono SVG (casa), fuente canónica |
| `frontend/public/favicon.ico` | Fallback para navegadores (16/32/48px) |
| `build/icon.ico` | Icono para el instalador y acceso directo (16–256px) |

Generación: `python scripts/generate_icon.py` (Pillow). Se ejecuta automáticamente en `build_windows_installer.py`.

### app/seeder.py

`seed_database(session, *, clean=False)` — semilla básica reusable que acepta un `Session` externo.
- `seed_demo_dataset(session, *, clean=False, years=3, seed=...)` — dataset completo de
  exploración: determinista (semilla), fechas relativas a hoy, numeración legal de facturas,
  impagos, rectificativa, baja lógica, movimientos bancarios confirmados/pendientes y perfil
  fiscal ausente para probar el salto de facturación.
- `scripts/seed.py` es un wrapper CLI (`--full`, `--clean`, `--years`, `--seed`) que llama a
  la función correspondiente y gestiona `commit()`.
- `desktop.py` llama a `seed_database` tras migraciones **solo** si `RENTAL_MGMT_DEMO=1` y
  `Owner` está vacío. Una instalación real arranca vacía.
- `_wipe_all` centraliza el borrado en orden seguro de claves foráneas (incluye
  `Reconciliation` y `EventLog`, y elimina antes las rectificativas por su índice parcial).

### Persistencia de datos en desinstalación

En `build/innosetup.iss`:
```
[Dirs]
Name: "{app}\data\db"; Flags: uninsneveruninstall
Name: "{app}\data\backups"; Flags: uninsneveruninstall
Name: "{app}\data\invoices"; Flags: uninsneveruninstall
```

### Bugs corregidos

- **IndexUpdateService.commit**: el servicio usaba `session.flush()` en lugar de `session.commit()`. La corrección fue añadir `session.commit()` + `session.refresh()` en el router (`leases.py`), no en el servicio. Esto mantiene el convenio de que los servicios solo llaman a `flush()` y los routers gestionan `commit()`.
- **EventLog table**: tuvo una etapa sin migración Alembic que impedía borrarla en `seed.py --clean`. Ya existe la migración `8c8362e4c3d6` y `_wipe_all` la incluye.
- **Wipe con rectificativas**: `_wipe_all` fallaba al poner `corrected_invoice_id=NULL` masivamente porque el índice parcial único de `(lease_id, period)` veía original y rectificativa como activas. Ahora se borran primero las rectificativas y después el resto.
- **Reconciliation UNIQUE**: `bank_movement_id` era `unique=True` y `propose_matches` insertaba varios candidatos → `IntegrityError`. Se eliminó la restricción, se limitan las propuestas persistidas y al confirmar se descartan las hermanas.
- **Estado de factura desincronizado**: editar o borrar un pago no recalculaba `paid`/`partial`. Ahora `PaymentService.update/delete` recalculan el estado (y se rechazan sobrepagos).
- **PDFs en CWD**: `INVOICES_DIR` era relativo; ahora sale de `DATA_ROOT` (`app/config.py`).
- **Facturas sin `TaxProfile`**: abortaban todo el lote; ahora se omiten y se registran en el log; la unicidad `(lease_id, period)` está garantizada por índice parcial.
- **Colisión SPA/API**: la API vivía en rutas raíz y rompía los deep links; ahora todo cuelga de `/api`.
- **Backup inconsistente con WAL**: se usa la API de backup de SQLite + `integrity_check`.
- **`POST /invoices/generate` devolvía `{}`**: tras `commit()` las instancias ORM quedaban expiradas y la serialización no las recargaba. Ahora el router hace `refresh()` de cada factura antes de responder.
- **`GET /invoices/{id}` no devolvía `lines`**: SQLModel no serializa relaciones al usar `model_dump`; el router construye ahora un payload explícito (`_invoice_payload`) con las líneas.
- **Pago sobre rectificativa**: un importe total ≤ 0 hacía que `_update_invoice_status` marcara la factura como `paid` con 0 pagos. Ahora se rechazan pagos sobre facturas sin importe positivo y el estado de rectificativas nunca auto-transiciona.
- **Facturas legales sin numerar**: el número `INV-{año}-{id}` se calculaba al vuelo en el PDF, no se persistía y no era correlativo por serie. Ahora `InvoiceNumberingService` asigna y persiste `series/sequence/number/fiscal_year` (migración `a9e3f7c1d5b2` con backfill de las existentes).
- **Gastos sin IVA**: no había forma de registrar el IVA soportado, así que el 303 no podía calcularlo. Ahora `Expense` tiene `vat_rate`/`vat_amount` opcionales (migración `c1f8a2e6d4b9`); `ExpenseService` calcula la cuota incluida en el importe total y `ExpenseService.update` la recalcula al cambiar importe o tipo.
- **E2E con datos resucitados por WAL**: `playwright.config.ts` solo borraba `*.db`; los ficheros `-wal`/`-shm` de la ejecución anterior resucitaban filas al recrear la base. Ahora se borran los tres.

## Convenios del proyecto

- **Lógica en services/**: toda la lógica de negocio va en `app/services/`, nunca en modelos ni routers
- **Routers finos**: los endpoints FastAPI solo llaman a servicios y serializan respuestas
- **Decimal para dinero**: usar `Decimal`, nunca `float` para importes
- **Soft-delete**: `deleted_at IS NULL` para registros activos. Nunca borrar datos contables
- **Migraciones**: toda creación/modificación de esquema vía Alembic, nunca `create_all`
- **Transacciones**: los servicios reciben `session` externamente (injection)
- **Tests**: usar SQLite in-memory via fixtures, sesión limpia por test, con `foreign_keys=ON`
- **Alembic migrations**: añadir `import sqlmodel` manualmente al generarlas (limitación de SQLModel)
- **SQLite**: PRAGMAs `foreign_keys=ON`, `journal_mode=WAL` y `busy_timeout` en `app/database.create_db_engine`
- **API bajo `/api`**: los routers se montan con `prefix="/api"`; el frontend usa `baseURL: '/api'`
- **Facturas**: numerar **solo al emitir** (`InvoiceNumberingService`), nunca modificar el número; prohibido borrar facturas (usar rectificativa). El PDF usa el número y el snapshot persistidos, no datos vivos.
- **Informes fiscales**: `FiscalService` computa facturas por **fecha de expedición** (las rectificativas en el trimestre de emisión) y gastos por **fecha del gasto**. El 303 solo cuenta el IVA de gastos deducibles; el 100 usa la base sin IVA como ingreso. Los informes son orientativos y devuelven importes como strings (`"123.45"`).
- **Cobertura**: `pytest` exige ≥80 % en `app/services` vía `--cov-fail-under=80`
- **Frontend**: TanStack Query para datos (sin `useFetch` ad-hoc), TypeScript `strict`, ESLint limpio

## Estructura del proyecto

```
rental-mgmt/
├── app/
│   ├── models/        → SQLModel entities
│   ├── services/      → Lógica de negocio
│   ├── api/           → Routers FastAPI
│   │   └── routers/   → leases, invoices, payments, expenses,
│   │                   owners, tenants, properties, units,
│   │                   reconciliation, stats, fiscal
│   ├── jobs/          → APScheduler jobs
│   └── seeder.py      → Reusable seed logic (llamado por desktop.py y scripts/seed.py)
├── frontend/
│   ├── src/
│   │   ├── api/       → Axios client, endpoints, queryKeys, queryClient
│   │   ├── pages/     → Dashboard, Leases, Invoices, Payments, Expenses, Fiscal...
│   │   ├── components/→ AppLayout, CrudPage, formularios, ErrorBoundary
│   │   ├── types/     → TypeScript interfaces
│   │   └── utils/     → format, labels compartidos
│   └── e2e/           → Playwright E2E tests (10)
├── data/
│   ├── db/            → SQLite database WAL (ignorada por git)
│   ├── backups/       → Backups con integrity_check
│   └── invoices/      → PDFs generados
├── tests/             → Pytest tests (202, cov ≥80 % services)
├── alembic/           → Migraciones
├── scripts/           → Build instalador, docs, icono, seed
├── build/
│   └── innosetup.iss  → InnoSetup installer config
├── rental-mgmt.spec   → PyInstaller spec (onedir)
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
12. ✅ **Fase 11** — Consolidación (integridad SQLite, bugs de dinero, API `/api`, packaging único, TanStack Query)
13. 🔄 **Fase 12** — Fiscal/CRM:
    - ✅ **12.1** — Factura legal (numeración por serie/ejercicio, vencimiento, snapshot fiscal, rectificativas)
    - ✅ **12.2** — Informes fiscales (303/190/100) + IVA opcional en gastos (`vat_rate`/`vat_amount`)
    - ⏳ **12.3** — Avisos de impago y actividad
    - ⏳ **12.4** — Plazos de fianza
    - CRM descartado de la fase (sin caso de uso claro)
