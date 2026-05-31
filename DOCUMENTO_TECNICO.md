# Documento Técnico — rental-mgmt

> Generado automáticamente por `scripts/generate_docs.py`. No editar manualmente.

## 1. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Runtime | Python ≥ 3.11 |
| Dependencias principales | , fastapi, uvicorn[standard], sqlmodel, alembic, apscheduler, reportlab, jinja2, python-dotenv, python-multipart, pytest, pytest-asyncio, ruff |
| Dependencias de desarrollo | pytest, pytest-asyncio, ruff |

## 2. Estructura del proyecto

```
rental-mgmt/
├── alembic/
    ├── versions/
        ├── 20260531_0155_2e4d256a59c2_create_core_models.py
        └── 20260531_0226_0928999bac08_add_index_update_table.py
    ├── env.py
    └── script.py.mako
├── app/
    ├── api/
    ├── jobs/
    ├── models/
        ├── base.py
        ├── lease.py
        ├── owner.py
        ├── property.py
        ├── tenant.py
        └── unit.py
    ├── services/
        ├── index_update_service.py
        └── lease_service.py
    ├── config.py
    ├── database.py
    ├── main.py
    └── seed.py
├── data/
    ├── db/
        └── rental.db
    ├── invoices/
├── scripts/
    └── generate_docs.py
├── tests/
    ├── conftest.py
    ├── test_index_update_service.py
    ├── test_lease_service.py
    └── test_sanity.py
├── .env
├── .env.example
├── .gitignore
├── AGENTS.md
├── DOCUMENTO_FUNCIONAL.md
├── DOCUMENTO_TECNICO.md
├── Dockerfile
├── README.md
├── REVISION_PLAN.md
├── alembic.ini
├── docker-compose.yml
├── opencode.jsonc
├── pyproject.toml
├── rental-mgmt-plan.md
└── rental_state_prompt.md
```

## 3. Modelos de datos (SQLModel)

Todas las entidades heredan de `AuditMixin` que aporta:
- `id`: Integer, PK, autoincrement
- `created_at`: DateTime, default UTC now
- `updated_at`: DateTime, default UTC now
- `deleted_at`: DateTime | None (soft-delete)

### Lease (`lease.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `unit_id` | int | No | → `unit.id` |
| `tenant_id` | int | No | → `tenant.id` |
| `owner_id` | int | No | → `owner.id` |
| `start_date` | date | No |  |
| `end_date` | Optional[date] | Sí |  |
| `is_active` | bool | No |  |
| `notes` | Optional[str] | Sí |  |

**Relaciones:**
- `unit` → 1:1 → `leases`
- `tenant` → 1:1 → `leases`
- `owner` → 1:1 → `leases`
- `rent_conditions` → 1:N → `lease`
- `tax_profile` → 1:1 → `lease`
- `deposit` → 1:1 → `lease`
- `index_updates` → 1:N → `lease`

### RentCondition (`lease.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `lease_id` | int | No | → `lease.id` |
| `start_date` | date | No |  |
| `monthly_rent` | Decimal | No |  |
| `notes` | Optional[str] | Sí |  |

**Relaciones:**
- `lease` → 1:1 → `rent_conditions`

### TaxProfile (`lease.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `lease_id` | int | No | → `lease.id` |
| `vat_rate` | Decimal | No |  |
| `irpf_rate` | Decimal | No |  |
| `vat_exempt` | bool | No |  |
| `withholding_applies` | bool | No |  |

**Relaciones:**
- `lease` → 1:1 → `tax_profile`

### Deposit (`lease.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `lease_id` | int | No | → `lease.id` |
| `amount` | Decimal | No |  |
| `deposit_date` | date | No |  |
| `agency` | str | No |  |
| `return_date` | Optional[date] | Sí |  |

**Relaciones:**
- `lease` → 1:1 → `deposit`

### IndexUpdate (`lease.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `lease_id` | int | No | → `lease.id` |
| `application_date` | date | No |  |
| `previous_rent` | Decimal | No |  |
| `new_rent` | Decimal | No |  |
| `index_rate` | Decimal | No |  |
| `index_name` | str | No |  |
| `notes` | Optional[str] | Sí |  |

**Relaciones:**
- `lease` → 1:1 → `index_updates`

### Owner (`owner.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `name` | str | No |  |
| `document_type` | str | No |  |
| `document_number` | str | No |  |
| `email` | str | No |  |
| `phone` | str | No |  |
| `address` | Optional[str] | Sí |  |

**Relaciones:**
- `properties` → 1:N → `owner`
- `leases` → 1:N → `owner`

### Property (`property.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `name` | str | No |  |
| `address` | str | No |  |
| `city` | str | No |  |
| `province` | str | No |  |
| `zip_code` | str | No |  |
| `cadastral_ref` | Optional[str] | Sí |  |
| `owner_id` | int | No | → `owner.id` |

**Relaciones:**
- `owner` → 1:1 → `properties`
- `units` → 1:N → `property`

### Tenant (`tenant.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `name` | str | No |  |
| `document_type` | str | No |  |
| `document_number` | str | No |  |
| `email` | str | No |  |
| `phone` | str | No |  |

**Relaciones:**
- `leases` → 1:N → `tenant`

### Unit (`unit.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `property_id` | int | No | → `property.id` |
| `name` | str | No |  |
| `unit_type` | str | No |  |
| `area_m2` | Optional[float] | Sí |  |
| `is_active` | bool | No |  |

**Relaciones:**
- `property` → 1:1 → `units`
- `leases` → 1:N → `unit`

## 4. Servicios

### IndexUpdateService

- **apply_index**(`session`, `lease_id`, `index_rate`, `application_date`, `index_name`, `notes`) → `tuple[RentCondition, IndexUpdate]`

### LeaseService

- **get_active_rent**(`session`, `lease_id`, `target_date`) → `Decimal`

## 5. Tests

**Total: 9 tests**

### Fixtures

- `session`
- `sample_lease`

### test_index_update_service.py — TestApplyIndex

| Test | Descripción |
|---|---|
| `test_apply_index_creates_new_rent_and_record` |  |
| `test_apply_index_multiple_times` |  |
| `test_apply_index_zero_rate` |  |

### test_lease_service.py — TestGetActiveRent

| Test | Descripción |
|---|---|
| `test_single_rent_condition` |  |
| `test_multiple_rent_conditions` |  |
| `test_no_rent_condition_raises` |  |
| `test_date_before_any_condition_raises` |  |
| `test_unknown_lease_raises` |  |
| `test_default_date` |  |

## 6. Migraciones (Alembic)

- **`2e4d256a`** → create core models
- **`0928999b`** → add index_update table
  - Padre: `2e4d256a`

```bash
alembic upgrade head    # Aplicar pendientes
alembic downgrade -1   # Revertir última
alembic history        # Ver historial
```

## 7. Comandos útiles

```bash
pytest -v                  # Ejecutar tests
ruff check .               # Lint
ruff check --fix .         # Auto-fix
python -m app.seed         # Cargar datos de prueba
python scripts/generate_docs.py  # Regenerar este documento
```
