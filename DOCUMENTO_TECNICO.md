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
        ├── 20260531_0226_0928999bac08_add_index_update_table.py
        ├── 20260531_1300_a16509918b31_add_invoice_and_invoice_line_tables.py
        └── 20260531_1305_bc191700d28c_add_payment_table.py
    ├── env.py
    └── script.py.mako
├── app/
    ├── api/
    ├── jobs/
    ├── models/
        ├── base.py
        ├── invoice.py
        ├── lease.py
        ├── owner.py
        ├── payment.py
        ├── property.py
        ├── tenant.py
        └── unit.py
    ├── services/
        ├── index_update_service.py
        ├── invoice_service.py
        ├── lease_service.py
        ├── payment_service.py
        └── pdf_service.py
    ├── config.py
    ├── database.py
    ├── main.py
    └── seed.py
├── data/
    ├── db/
        └── rental.db
    ├── invoices/
        ├── 2024/
            └── 06/
├── scripts/
    └── generate_docs.py
├── tests/
    ├── conftest.py
    ├── test_index_update_service.py
    ├── test_invoice_service.py
    ├── test_lease_service.py
    ├── test_payment_service.py
    ├── test_pdf_service.py
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

### Invoice (`invoice.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `period` | str | No |  |
| `lease_id` | int | No | → `lease.id` |
| `issue_date` | date | No |  |
| `status` | str | No |  |
| `total_base` | Decimal | No |  |
| `total_vat` | Decimal | No |  |
| `total_irpf_withholding` | Decimal | No |  |
| `total` | Decimal | No |  |
| `notes` | Optional[str] | Sí |  |

**Relaciones:**
- `lease` → 1:1 → `invoices`
- `lines` → 1:N → `invoice`
- `payments` → 1:N → `invoice`

### InvoiceLine (`invoice.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `invoice_id` | int | No | → `invoice.id` |
| `concept` | str | No |  |
| `base_amount` | Decimal | No |  |
| `vat_rate` | Decimal | No |  |
| `vat_amount` | Decimal | No |  |
| `irpf_rate` | Decimal | No |  |
| `irpf_withholding` | Decimal | No |  |

**Relaciones:**
- `invoice` → 1:1 → `lines`

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
- `invoices` → 1:N → `lease`

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

### Payment (`payment.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `invoice_id` | int | No | → `invoice.id` |
| `amount` | Decimal | No |  |
| `payment_date` | date | No |  |
| `method` | str | No |  |
| `notes` | Optional[str] | Sí |  |

**Relaciones:**
- `invoice` → 1:1 → `payments`

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

### InvoiceService

- **generate_monthly**(`session`, `period`) → `List[Invoice]`

### LeaseService

- **get_active_rent**(`session`, `lease_id`, `target_date`) → `Decimal`

### PaymentService

- **register**(`session`, `invoice_id`, `amount`, `payment_date`, `method`, `notes`) → `Payment`
- **_update_invoice_status**(`session`, `invoice`) → `None`

### PDFService

- **render_invoice**(`session`, `invoice_id`) → `Path`
- **_fmt**(`value`) → `str`

## 5. Tests

**Total: 23 tests**

### Fixtures

- `session`
- `sample_lease`

### test_index_update_service.py — TestApplyIndex

| Test | Descripción |
|---|---|
| `test_apply_index_creates_new_rent_and_record` |  |
| `test_apply_index_multiple_times` |  |
| `test_apply_index_zero_rate` |  |

### test_invoice_service.py — TestGenerateMonthly

| Test | Descripción |
|---|---|
| `test_vivienda_invoice_no_taxes` |  |
| `test_local_invoice_with_taxes` |  |
| `test_idempotent_does_not_duplicate` |  |
| `test_leases_without_tax_profile_raises` |  |
| `test_inactive_lease_ignored` |  |

### test_lease_service.py — TestGetActiveRent

| Test | Descripción |
|---|---|
| `test_single_rent_condition` |  |
| `test_multiple_rent_conditions` |  |
| `test_no_rent_condition_raises` |  |
| `test_date_before_any_condition_raises` |  |
| `test_unknown_lease_raises` |  |
| `test_default_date` |  |

### test_payment_service.py — TestRegisterPayment

| Test | Descripción |
|---|---|
| `test_full_payment_marks_invoice_paid` |  |
| `test_partial_payment_marks_invoice_partial` |  |
| `test_multiple_partial_payments_sum_to_paid` |  |
| `test_invoice_not_found_raises` |  |
| `test_zero_amount_raises` |  |
| `test_custom_method_and_notes` |  |

### test_pdf_service.py — TestRenderInvoice

| Test | Descripción |
|---|---|
| `test_pdf_generated_for_vivienda` |  |
| `test_pdf_generated_for_local` |  |
| `test_invoice_not_found_raises` |  |

## 6. Migraciones (Alembic)

- **`2e4d256a`** → create core models
- **`0928999b`** → add index_update table
  - Padre: `2e4d256a`
- **`a1650991`** → add invoice and invoice_line tables
  - Padre: `0928999b`
- **`bc191700`** → add payment table
  - Padre: `a1650991`

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
