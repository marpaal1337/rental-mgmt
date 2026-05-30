# 🏢 Plan de Gestión Inmobiliaria — `rental-mgmt`

> **Versión consolidada** · Single user · OSS · Local · España  
> Metodología: fases secuenciales con stop-point obligatorio

---

## 🧠 Principios

- Single user, uso local
- 100 % open source
- Sin sobreingeniería — funcionalidad por encima de arquitectura
- Sin microservicios
- Lógica siempre en `services/`, API siempre fina
- Pruebas desde el primer día (dinero de por medio)

---

## 🧱 Stack definitivo

| Capa | Tecnología | Por qué |
|---|---|---|
| Runtime | Python 3.11+ | — |
| API | FastAPI | — |
| ORM | SQLModel + Alembic | migraciones desde día 1 |
| Base de datos | **SQLite (WAL)** | single-user, backup = `cp fichero.db` |
| Scheduler | **APScheduler** (in-process) | sin broker, sin worker externo |
| PDF | WeasyPrint o ReportLab | WeasyPrint si Docker; ReportLab si nativo |
| Plantillas | Jinja2 | — |
| Linting | ruff | — |
| Tests | pytest | — |
| Infraestructura | Docker Compose (opcional) | útil para congelar entorno, no obligatorio |

> **Descartados del plan original**: PostgreSQL (innecesario para single-user), Celery + Redis (sobrecarga sin valor), Docker (opcional, no obligatorio).

---

## 📐 Estructura de carpetas objetivo

```
rental-mgmt/
├── app/
│   ├── models/        # SQLModel entities
│   ├── services/      # toda la lógica de negocio
│   ├── api/           # routers FastAPI (finos)
│   └── jobs/          # APScheduler jobs
├── data/
│   ├── db/            # rental.db (SQLite)
│   └── invoices/      # PDFs generados
├── templates/         # Jinja2
├── tests/
├── alembic/
├── pyproject.toml
└── docker-compose.yml (opcional)
```

---

## 🧾 Fiscalidad en España (crítico — no negociable)

El plan original hardcodeaba "local = sin IVA". **Esto es fiscalmente incorrecto.**

| Caso | IVA | IRPF |
|---|---|---|
| Vivienda habitual | Exenta | No aplica (PF→PF) |
| Local de negocio | **21 % repercutido** | **19 % retenido** si inquilino es empresa/profesional |
| Garaje / trastero independiente | 21 % | Variable |
| Alquiler turístico con servicios | 10 % | — |

**Solución**: entidad `TaxProfile` configurable por `Lease`, con campos `vat_rate`, `irpf_rate`, `vat_exempt`, `withholding_applies`. Nunca hardcodear tipos en `Invoice`.

---

## 🗂️ Modelo de datos completo

```
Owner ──< Property ──< Unit ──< Lease >── Tenant
                                 │
                                 ├── RentCondition (histórico de rentas)
                                 ├── TaxProfile (fiscalidad por contrato)
                                 ├── Deposit (fianza)
                                 └── IndexUpdate (revisiones IPC/IRAV)

Lease ──< Invoice ──< InvoiceLine
Invoice ──< Payment

Property ──< Expense (gastos: IBI, comunidad, seguro…)

BankMovement ──< Reconciliation >── Payment
```

---

## 🚀 Fases

---

### FASE 0 — Bootstrap

**Objetivo**: entorno reproducible, tests y linting configurados antes de escribir una línea de negocio.

**Tareas**:
- `pyproject.toml` con todas las dependencias
- FastAPI hello world
- SQLite + Alembic inicializado
- pytest configurado con un test de sanidad
- ruff configurado
- Estructura `app/{models,services,api,jobs}` creada (vacía)
- `.env.example` con `DATABASE_URL`, `SECRET_KEY`
- `docker-compose.yml` opcional

**Output**: proyecto arranca, `pytest` pasa, `ruff check .` sin errores.

**⛔ STOP — esperar confirmación**

---

### FASE 1 — Modelo core

**Objetivo**: definir y persistir el modelo de datos mínimo funcional.

**Entidades**:
- `Owner` — arrendador (puede haber varios titulares: persona física, sociedad)
- `Property` — inmueble
- `Unit` — unidad alquilable dentro de un inmueble
- `Tenant` — inquilino
- `Lease` — **entidad central**, vincula Unit + Tenant + Owner
- `RentCondition` — histórico de renta (permite revisiones IPC)
- `TaxProfile` — perfil fiscal por contrato (`vat_rate`, `irpf_rate`, `vat_exempt`, `withholding_applies`)
- `Deposit` — fianza: importe, fecha depósito, organismo autonómico, fecha devolución

**Reglas**:
- Alembic migration desde el primer modelo (no `create_all`)
- Soft-delete + `created_at` / `updated_at` en todas las entidades con datos contables
- Seed: 1 owner, 1 property, 1 unit vivienda + 1 unit local, 2 leases con TaxProfile distintos

**Output**: tablas creadas vía migración, seed ejecutable.

**⛔ STOP — esperar confirmación**

---

### FASE 2 — LeaseService

**Objetivo**: calcular la renta vigente de un contrato en una fecha dada.

**Tareas**:
- `LeaseService.get_active_rent(lease_id, date) -> Decimal`
- Aplica la `RentCondition` vigente en esa fecha
- `IndexUpdateService.apply_index(lease_id, index_rate, date)` — registra una revisión IPC/IRAV
- Tests unitarios obligatorios para ambos servicios

**Reglas**: sin facturación, sin API compleja. Solo lógica pura de contratos.

**Output**: función testada que dado un lease + fecha devuelve renta actual.

**⛔ STOP — esperar confirmación**

---

### FASE 3 — Facturación con fiscalidad correcta

**Objetivo**: generar facturas mensuales con IVA e IRPF correctos según el TaxProfile del contrato.

**Entidades**:
- `Invoice` — periodo `YYYY-MM`, `lease_id`, estado (`draft` / `issued` / `paid` / `cancelled`)
- `InvoiceLine` — concepto, base imponible, tipo IVA, cuota IVA, tipo IRPF, retención IRPF

**Servicios**:
- `InvoiceService.generate_monthly(period: str)` — genera facturas para todos los leases activos
- Consulta `TaxProfile` del lease para aplicar IVA 21 % (local), IRPF 19 % si aplica, exento si vivienda

**Reglas**:
- Una factura por lease por periodo, idempotente (no duplicar si ya existe)
- Sin PDF todavía
- Tests: generar factura de vivienda (sin impuestos) y de local (IVA + IRPF)

**Output**: facturas en DB con líneas fiscalmente correctas.

**⛔ STOP — esperar confirmación**

---

### FASE 4 — PDF de factura (adelantada)

**Objetivo**: convertir cada factura en un documento enviable al inquilino. Aquí el sistema empieza a ser útil de verdad.

**Tareas**:
- Plantilla Jinja2 para factura (datos arrendador, arrendatario, líneas, totales, pie fiscal)
- Render a PDF con WeasyPrint o ReportLab
- Almacenamiento en `data/invoices/{year}/{month}/{invoice_id}.pdf`
- `PDFService.render_invoice(invoice_id) -> Path`

**Output**: PDF descargable por cada factura generada.

**⛔ STOP — esperar confirmación**

---

### FASE 5 — Pagos

**Objetivo**: registrar pagos y actualizar el estado de las facturas.

**Entidades**:
- `Payment` — `invoice_id`, `amount`, `date`, `method`, `notes`

**Servicios**:
- `PaymentService.register(invoice_id, amount, date)` — registra pago y actualiza estado de la factura
- Estado de factura derivado: `paid` si importe cubierto, `partial` si no

**Matching**: por `invoice_id` directo (conciliación bancaria viene en Fase 7).

**Output**: facturas con estado actualizado tras pago.

**⛔ STOP — esperar confirmación**

---

### FASE 6 — Gastos

**Objetivo**: registrar gastos del inmueble para calcular rentabilidad real y preparar la declaración IRPF.

**Entidades**:
- `Expense` — `property_id` o `lease_id`, categoría (IBI / comunidad / seguro / reparación / suministros / otros), importe, fecha, repercutible al inquilino (sí/no), factura asociada

**Servicios**:
- `ExpenseService.summary(property_id, year)` — ingresos vs gastos, rentabilidad neta
- Distinción entre gastos deducibles y no deducibles (para modelo 100 IRPF)

**Output**: gastos registrados, resumen de rentabilidad por inmueble.

**⛔ STOP — esperar confirmación**

---

### FASE 7 — Conciliación bancaria

**Objetivo**: importar movimientos bancarios y emparejarlos con pagos registrados.

**Entidades**:
- `BankMovement` — fecha, importe, concepto, IBAN origen, estado (`unmatched` / `proposed` / `confirmed`)
- `Reconciliation` — vincula `BankMovement` ↔ `Payment`, score de coincidencia

**Tareas**:
- CSV importer (empezar con un banco: ING, BBVA o Santander — tú eliges)
- Interfaz de adaptadores para añadir más bancos después
- Matching con score: importe exacto + concepto fuzzy + IBAN origen recurrente + ventana de fechas (±5 días respecto a vencimiento)
- Estado `propuesto/confirmado`: el sistema propone, el usuario confirma. **Nunca auto-aplicar matches dudosos.**

**Output**: conciliación básica funcional con revisión manual.

**⛔ STOP — esperar confirmación**

---

### FASE 8 — API REST completa

**Objetivo**: exponer toda la funcionalidad vía endpoints.

**Endpoints mínimos**:
- `GET/POST /leases`
- `GET/POST /invoices`
- `POST /invoices/generate`
- `GET /invoices/{id}/pdf`
- `GET/POST /payments`
- `POST /reconciliation/import`
- `GET/POST /expenses`

**Reglas**:
- API fina: sin lógica compleja, solo llamadas a services
- Auth básica: token estático en `.env` (single-user, no OAuth)

**⛔ STOP — esperar confirmación**

---

### FASE 9 — Automatización

**Objetivo**: jobs automáticos sin infraestructura externa.

**Tareas**:
- APScheduler configurado dentro del proceso FastAPI
- Job mensual: `generar_facturas_mensuales(period)`
- Job diario: `detectar_impagos()` — facturas vencidas sin pago
- `EventLog` — tabla de registro de eventos del sistema (auditoría de jobs)

**Output**: sistema genera facturas solo cada mes, alerta impagos cada día.

**⛔ STOP — esperar confirmación**

---

### FASE 10 — Calidad y cierre

**Objetivo**: hacer el sistema mantenible y robusto a largo plazo.

**Tareas**:
- Backups automáticos: cron diario que copia `rental.db` a carpeta sincronizada (Dropbox/iCloud/Google Drive) con retención de 7 días
- Soft-delete completo + columnas de auditoría en todas las mutaciones contables
- UI básica (a decidir): HTMX + Jinja2 desde el mismo FastAPI para listar contratos, facturas, pagos y marcar cobros a mano — cero JS, cero framework frontend. Alternativa: Swagger es suficiente si no se quiere UI.
- Cobertura de tests: mínimo 80 % en `services/`

**Output**: sistema estable, con backups y UI mínima funcional.

---

## 🔒 Reglas críticas (nunca romper)

- No diseñar todo desde el inicio
- No crear microservicios
- No añadir features no solicitadas en cada fase
- Siempre terminar cada fase y esperar confirmación antes de continuar
- Lógica siempre en `services/`, nunca en routers ni modelos
- Alembic para **todas** las migraciones, nunca `create_all` en producción
- Nunca auto-confirmar un match de conciliación bancaria

---

## 🎯 Definición de éxito

El sistema puede:

1. Crear contratos con perfil fiscal correcto (vivienda / local)
2. Generar facturas mensuales con IVA e IRPF según la ley española
3. Exportar PDF de cada factura listo para enviar al inquilino
4. Registrar pagos y actualizar estado de facturas
5. Registrar gastos y calcular rentabilidad neta por inmueble
6. Conciliar movimientos bancarios con revisión manual
7. Automatizar facturación y alertas de impago sin intervención

Todo funcionando en local, sin dependencias externas de pago.

---

## 📋 Decisiones abiertas (responder antes de Fase 0)

| Decisión | Opciones | Recomendación |
|---|---|---|
| PDF engine | WeasyPrint (Docker) vs ReportLab (nativo) | WeasyPrint si usas Docker; ReportLab si nativo en Windows |
| Banco para CSV importer (Fase 7) | ING / BBVA / Santander / otro | El que uses habitualmente |
| UI en Fase 10 | HTMX + Jinja2 vs solo Swagger | HTMX si quieres algo visual; Swagger si te basta la API |
| Nombre del proyecto | `rental-mgmt`, `alquiler-pro`, otro | Cualquiera sin espacios ni typos — renombrar antes de Fase 0 |
