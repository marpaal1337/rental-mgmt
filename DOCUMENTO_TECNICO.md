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
        ├── 20260531_1305_bc191700d28c_add_payment_table.py
        ├── 20260531_1309_e1cd76ded677_add_expense_table.py
        └── 20260531_1311_1c44557ef4b6_add_bank_movement_and_reconciliation_.py
    ├── env.py
    └── script.py.mako
├── app/
    ├── api/
        ├── routers/
            ├── expenses.py
            ├── invoices.py
            ├── leases.py
            ├── pages.py
            ├── payments.py
            └── reconciliation.py
        ├── deps.py
        └── schemas.py
    ├── jobs/
        ├── daily_backup.py
        ├── daily_overdue.py
        ├── monthly_invoicing.py
        └── scheduler.py
    ├── models/
        ├── bank.py
        ├── base.py
        ├── event_log.py
        ├── expense.py
        ├── invoice.py
        ├── lease.py
        ├── owner.py
        ├── payment.py
        ├── property.py
        ├── tenant.py
        └── unit.py
    ├── services/
        ├── backup_service.py
        ├── bank_adapter.py
        ├── expense_service.py
        ├── index_update_service.py
        ├── invoice_service.py
        ├── lease_service.py
        ├── payment_service.py
        ├── pdf_service.py
        └── reconciliation_service.py
    ├── templates/
        ├── base.html
        ├── dashboard.html
        ├── expenses.html
        ├── invoices.html
        ├── leases.html
        └── payments.html
    ├── config.py
    ├── database.py
    ├── main.py
    └── seed.py
├── data/
    ├── backups/
        ├── rental_20260531_115909.db
        ├── rental_20260531_120051.db
        ├── rental_20260531_120056.db
        ├── rental_20260531_120345.db
        └── rental_20260531_120353.db
    ├── db/
        └── rental.db
    ├── invoices/
        ├── 2024/
            └── 06/
├── scripts/
    └── generate_docs.py
├── tests/
    ├── conftest.py
    ├── test_api.py
    ├── test_backup_service.py
    ├── test_bank_adapter.py
    ├── test_coverage_gaps.py
    ├── test_expense_service.py
    ├── test_index_update_service.py
    ├── test_invoice_service.py
    ├── test_jobs.py
    ├── test_lease_service.py
    ├── test_pages.py
    ├── test_payment_service.py
    ├── test_pdf_service.py
    ├── test_reconciliation_service.py
    └── test_sanity.py
├── .coverage
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

### BankMovement (`bank.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `entry_date` | date | No |  |
| `value_date` | Optional[date] | Sí |  |
| `amount` | Decimal | No |  |
| `concept` | str | No |  |
| `iban_origin` | Optional[str] | Sí |  |
| `reference` | Optional[str] | Sí |  |
| `status` | str | No |  |
| `raw_data` | Optional[str] | Sí |  |

**Relaciones:**
- `reconciliation` → 1:1 → `bank_movement`

### Reconciliation (`bank.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `bank_movement_id` | int | No | → `bank_movement.id` |
| `payment_id` | int | No | → `payment.id` |
| `score` | Decimal | No |  |
| `confirmed_at` | Optional[datetime] | Sí |  |
| `notes` | Optional[str] | Sí |  |

**Relaciones:**
- `bank_movement` → 1:1 → `reconciliation`
- `payment` → 1:1 → `reconciliations`

### EventLog (`event_log.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `event_type` | str | No |  |
| `description` | str | No |  |
| `details` | Optional[str] | Sí |  |
| `level` | str | No |  |

### Expense (`expense.py`)

| Campo | Tipo | Nulo | FK |
|---|---|---|---|
| `property_id` | int | No | → `property.id` |
| `lease_id` | Optional[int] | Sí | → `lease.id` |
| `category` | str | No |  |
| `amount` | Decimal | No |  |
| `expense_date` | date | No |  |
| `deductible` | bool | No |  |
| `supplier` | Optional[str] | Sí |  |
| `invoice_number` | Optional[str] | Sí |  |
| `notes` | Optional[str] | Sí |  |

**Relaciones:**
- `property` → 1:1 → `expenses`
- `lease` → 1:1 → `expenses`

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
- `expenses` → 1:N → `lease`

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
- `reconciliations` → 1:N → `payment`

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
- `expenses` → 1:N → `property`

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

### BackupService

- **_db_path**() → `Path`
- **run_backup**() → `Path`
- **clean_old_backups**(`retention_days`) → `int`

### BankRow

- **__init__**(`entry_date`, `concept`, `amount`, `value_date`, `iban_origin`, `reference`, `raw`) → `None`

### BaseBankAdapter

- **parse**(`file_path`) → `list[BankRow]`

### GenericBankAdapter

- **__init__**(`delimiter`, `date_format`, `encoding`, `skip_rows`, `col_date`, `col_concept`, `col_amount`, `col_iban`, `col_reference`) → `None`
- **parse**(`file_path`) → `list[BankRow]`
- **_parse_date**(`raw`) → `date`

### INGBankAdapter

- **__init__**() → `None`

### ExpenseService

- **register**(`session`, `property_id`, `category`, `amount`, `expense_date`, `lease_id`, `deductible`, `supplier`, `invoice_number`, `notes`) → `Expense`
- **list_by_property**(`session`, `property_id`, `year`) → `list[Expense]`
- **summary**(`session`, `property_id`, `year`) → `dict`

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

### ReconciliationService

- **import_csv**(`session`, `file_path`, `adapter`) → `list[BankMovement]`
- **propose_matches**(`session`, `bank_movement_id`) → `list[Reconciliation]`
- **_match_score**(`movement`, `payment`) → `Decimal`
- **confirm_match**(`session`, `reconciliation_id`) → `Reconciliation`
- **list_unmatched**(`session`) → `list[BankMovement]`
- **list_proposed**(`session`) → `list[BankMovement]`

## 5. Tests

**Total: 77 tests**

### Fixtures

- `session`
- `client`
- `sample_lease`

### test_api.py — TestAuth

| Test | Descripción |
|---|---|
| `test_no_key_returns_403` |  |
| `test_invalid_key_returns_403` |  |
| `test_valid_key_allows_access` |  |

### test_api.py — TestLeases

| Test | Descripción |
|---|---|
| `test_list_leases` |  |
| `test_get_lease_not_found` |  |

### test_api.py — TestInvoices

| Test | Descripción |
|---|---|
| `test_generate_without_data_returns_empty` |  |

### test_api.py — TestExpenses

| Test | Descripción |
|---|---|
| `test_categories` |  |
| `test_register_no_property_returns_error` |  |

### test_api.py — TestReconciliation

| Test | Descripción |
|---|---|
| `test_unmatched_returns_empty_list` |  |
| `test_movements_empty` |  |

### test_api.py — TestHealth

| Test | Descripción |
|---|---|
| `test_health` |  |
| `test_root` |  |

### test_backup_service.py — TestBackupService

| Test | Descripción |
|---|---|
| `test_backup_creates_file` |  |
| `test_clean_old_backups` |  |

### test_bank_adapter.py — TestGenericBankAdapter

| Test | Descripción |
|---|---|
| `test_parse_basic_csv` |  |
| `test_parse_with_skip_rows` |  |
| `test_empty_line_skipped` |  |

### test_bank_adapter.py — TestINGBankAdapter

| Test | Descripción |
|---|---|
| `test_parse_ing_format` |  |

### test_coverage_gaps.py — TestIndexUpdateServiceCoverage

| Test | Descripción |
|---|---|
| `test_lease_not_found` |  |

### test_coverage_gaps.py — TestPaymentServiceCoverage

| Test | Descripción |
|---|---|
| `test_payment_status_stays_draft_when_no_payments` |  |

### test_coverage_gaps.py — TestPDFServiceCoverage

| Test | Descripción |
|---|---|
| `test_invoice_no_lines_raises` |  |
| `test_owner_with_address_in_pdf` |  |

### test_coverage_gaps.py — TestReconciliationCoverage

| Test | Descripción |
|---|---|
| `test_skip_already_confirmed_payment` |  |
| `test_concept_match_contributes_score` |  |

### test_expense_service.py — TestRegister

| Test | Descripción |
|---|---|
| `test_register_valid_expense` |  |
| `test_register_with_lease` |  |
| `test_property_not_found_raises` |  |
| `test_invalid_category_raises` |  |
| `test_zero_amount_raises` |  |
| `test_lease_not_found_raises` |  |

### test_expense_service.py — TestListByProperty

| Test | Descripción |
|---|---|
| `test_list_by_property` |  |
| `test_list_by_property_and_year` |  |
| `test_property_not_found_raises` |  |

### test_expense_service.py — TestSummary

| Test | Descripción |
|---|---|
| `test_summary_no_income_no_expenses` |  |
| `test_summary_with_expenses` |  |
| `test_summary_with_income` |  |
| `test_summary_property_not_found_raises` |  |

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

### test_jobs.py — TestGenerateMonthlyInvoices

| Test | Descripción |
|---|---|
| `test_produces_event_log_on_success` |  |
| `test_logs_error_on_failure` |  |

### test_jobs.py — TestDetectOverdue

| Test | Descripción |
|---|---|
| `test_detects_old_unpaid_invoices` |  |
| `test_recent_invoice_not_overdue` |  |
| `test_paid_invoice_not_overdue` |  |
| `test_logs_events_when_overdue_found` |  |

### test_lease_service.py — TestGetActiveRent

| Test | Descripción |
|---|---|
| `test_single_rent_condition` |  |
| `test_multiple_rent_conditions` |  |
| `test_no_rent_condition_raises` |  |
| `test_date_before_any_condition_raises` |  |
| `test_unknown_lease_raises` |  |
| `test_default_date` |  |

### test_pages.py — TestPages

| Test | Descripción |
|---|---|
| `test_dashboard` |  |
| `test_leases_page` |  |

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

### test_reconciliation_service.py — TestImportCSV

| Test | Descripción |
|---|---|
| `test_import_creates_movements` |  |
| `test_import_with_iban` |  |

### test_reconciliation_service.py — TestProposeMatches

| Test | Descripción |
|---|---|
| `test_exact_match_found` |  |
| `test_no_match_different_amount` |  |
| `test_movement_not_found_raises` |  |
| `test_movement_already_confirmed_raises` |  |

### test_reconciliation_service.py — TestConfirmMatch

| Test | Descripción |
|---|---|
| `test_confirm_updates_status` |  |
| `test_not_found_raises` |  |

### test_reconciliation_service.py — TestListUnmatched

| Test | Descripción |
|---|---|
| `test_list_unmatched` |  |

## 6. Migraciones (Alembic)

- **`2e4d256a`** → create core models
- **`0928999b`** → add index_update table
  - Padre: `2e4d256a`
- **`a1650991`** → add invoice and invoice_line tables
  - Padre: `0928999b`
- **`bc191700`** → add payment table
  - Padre: `a1650991`
- **`e1cd76de`** → add expense table
  - Padre: `bc191700`
- **`1c44557e`** → add bank_movement and reconciliation tables
  - Padre: `e1cd76de`

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
