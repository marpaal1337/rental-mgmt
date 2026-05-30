# Revisión del plan `rental_state_prompt.md`

Mi veredicto: el plan tiene una **metodología muy buena** (fases con stop-points, sin sobreingeniería) pero **el stack está sobredimensionado para single-user** y el **modelo fiscal/legal es incorrecto para España**. A continuación, lo que conservaría, lo que cambiaría y una propuesta de plan revisado.

---

## 1. Lo que está bien y conviene mantener

- **Fases secuenciales con stop-point**: evita el clásico "sistema diseñado entero que nunca arranca". Mantenerlo.
- **Lease como entidad central** y `RentCondition` como histórico de renta: correcto, permite IPC y revisiones.
- **Lógica en services, API fina**: separación adecuada para FastAPI.
- **Single user + 100% OSS + local**: alcance realista.

---

## 2. Problemas detectados

### 2.1 Stack sobredimensionado (ya confirmado simplificar)
El plan exige PostgreSQL + Celery + Redis + Docker para un caso single-user. Eso introduce 4 piezas que no aportan valor a un usuario único gestionando sus pisos:

- **PostgreSQL → SQLite**: para single-user es suficiente, sin servidor, fichero único, backup = `cp`.
- **Celery + Redis → APScheduler**: jobs in-process, sin broker, sin worker. Mucho menos código y operativa.
- **Docker → opcional**: útil sólo si quieres congelar el entorno; un `uv`/`venv` local es más rápido para iterar.
- **WeasyPrint en Windows**: tiene dependencias nativas (GTK/Cairo/Pango) molestas. Alternativas: **ReportLab**, **xhtml2pdf**, o WeasyPrint *sólo* si corres en Docker.

### 2.2 Modelo fiscal incorrecto para España
El plan dice literalmente *"local = sin IVA"*. **Esto es falso** y rompería tus facturas reales:

| Caso | IVA | Retención IRPF |
|------|-----|----------------|
| **Vivienda habitual** | Exenta | No (si arrendador persona física y inquilino persona física) |
| **Local de negocio** | **21% repercutido** | **19% retenido** si inquilino es empresa/profesional |
| **Garaje/trastero independiente** | 21% | Variable |
| **Alquiler turístico con servicios** | 10% | — |

**Conclusión**: la fiscalidad no puede hardcodearse en `Invoice` por tipo `vivienda/local`. Debe ser un **`TaxProfile` configurable por `Lease`** (campos: `vat_rate`, `irpf_rate`, `vat_exempt`, `withholding_applies`).

### 2.3 Faltan entidades clave para gestión real
El modelo de Fase 1 cubre lo básico pero olvida cosas que **vas a necesitar en el primer trimestre de uso real**:

- **`Owner`** (arrendador). Aunque seas single-user, te puede interesar facturar desde varios titulares (tú, tu cónyuge, una sociedad).
- **`Deposit` (fianza)**: en España es obligatorio depositar en organismo autonómico (IVIMA en Madrid, INCASOL en Cataluña…). Mínimo: importe, fecha depósito, organismo, fecha devolución.
- **`Expense`** (gastos): comunidad, IBI, basuras, seguro, suministros. Algunos repercutibles al inquilino, otros no. Indispensable para saber rentabilidad real y para Hacienda (declaración IRPF inmuebles arrendados).
- **`IndexUpdate`** (IPC/IGC/IRAV): la actualización anual de renta. Mejor un servicio que registre el índice aplicado, no calcular sobre la marcha.
- **`Document`**: PDFs del contrato firmado, DNI del inquilino, justificante de fianza. Sin esto el sistema sirve para facturar pero no para *gestionar*.

### 2.4 Orden de fases subóptimo
**PDF en Fase 7 es demasiado tarde**. Una factura sin PDF no se envía al inquilino: el sistema no es usable hasta entonces. Adelantar PDF a inmediatamente después de la Fase 3 (facturación) hace que tras Fase 3+PDF ya tengas valor real.

### 2.5 Conciliación bancaria demasiado naïve
Match por *importe + concepto* tendrá falsos positivos (dos inquilinos pagan el mismo importe). Añadir:

- **Ventana de fechas** (±N días respecto a vencimiento factura).
- **Score de coincidencia** (importe exacto + concepto fuzzy + cuenta origen recurrente).
- **Estado `propuesto/confirmado`**: el sistema propone, tú confirmas. Nunca auto-aplicar matches dudosos en datos contables.
- **Formato CSV canónico + adaptadores por banco** (BBVA, Santander, ING usan layouts distintos). Empezar con uno sólo y dejar la interfaz abierta.

### 2.6 Omisiones de calidad
- **Sin estrategia de tests**: para algo que toca dinero, mínimo pytest sobre los services (cálculo de renta, generación de factura, matching).
- **Sin backups**: con SQLite, cron diario que copia el `.db` a otra carpeta + retención semanal.
- **Sin auditoría/log**: cualquier mutación en `Invoice`/`Payment` debería dejar rastro (created_at, updated_at, deleted soft).

### 2.7 Detalle menor: nombre del proyecto
La carpeta se llama `rental state` — probablemente quisiste decir **`real estate`** o `rental-management`. Renombrar antes de empezar evita arrastrar el typo en repos, contenedores e imports.

---

## 3. Propuesta de plan revisado

Mismo espíritu de fases con stop-point, pero ajustado a single-user + España.

### Stack final propuesto
- Python 3.11 + FastAPI + SQLModel
- **SQLite** (file-based, con WAL)
- **APScheduler** (in-process)
- **Alembic** (migraciones desde el día 1)
- **ReportLab** o WeasyPrint-en-Docker para PDF
- **pytest** + **ruff** desde Fase 0
- Docker **opcional** (sólo si quieres reproducibilidad)

### Fases revisadas

- **Fase 0 — Bootstrap** (nueva): repo, `pyproject.toml`, FastAPI hello, SQLite + Alembic, pytest configurado, ruff, estructura `app/{models,services,api,jobs}`. *Stop.*
- **Fase 1 — Modelo core ampliado**: `Owner`, `Property`, `Unit`, `Tenant`, `Lease`, `RentCondition`, `Deposit`, `TaxProfile`. Seed con 1 owner, 1 propiedad, 1 lease vivienda + 1 lease local. *Stop.*
- **Fase 2 — LeaseService**: renta vigente por fecha, aplicación de `RentCondition`, servicio `IndexUpdateService` para revisión IPC. *Stop.*
- **Fase 3 — Facturación con fiscalidad correcta**: `Invoice` + `InvoiceLine`, `InvoiceService.generate_monthly(period)` consultando `TaxProfile` del lease (IVA 21% local, IRPF 19% si aplica, exento vivienda). *Stop.*
- **Fase 4 — PDF de factura** (adelantada): plantilla Jinja2, render a PDF, almacenamiento en `data/invoices/`. Ya tienes valor real: facturas enviables. *Stop.*
- **Fase 5 — Pagos**: `Payment`, `PaymentService.register(invoice_id, amount, date)`, estado factura derivado. *Stop.*
- **Fase 6 — Gastos**: `Expense` (comunidad/IBI/seguro/suministros), repercutibles vs no, vinculables a `Property` o `Lease`. Imprescindible para rentabilidad y declaración. *Stop.*
- **Fase 7 — Conciliación bancaria**: `BankMovement`, importer CSV (un banco al inicio), matching con score y ventana de fechas, estado `propuesto/confirmado`. *Stop.*
- **Fase 8 — API REST completa + auth básica local** (token estático en `.env`). *Stop.*
- **Fase 9 — Automatización**: APScheduler con jobs `generar_facturas_mensuales` y `detectar_impagos`. Tabla `EventLog`. *Stop.*
- **Fase 10 — Calidad**: backups SQLite programados, soft-delete + audit columns, dashboard simple (decidir HTMX/Jinja vs sólo Swagger). *Final.*

---

## 4. Decisiones aún abiertas

- **UI**: no la confirmaste. Mi recomendación con tu perfil (uso real personal): **HTMX + Jinja2** mínimo en Fase 10 — cero JS, sirve desde el mismo FastAPI, suficiente para listar inmuebles/contratos/facturas y marcar pagos a mano. Si te basta Swagger, omite Fase 10-UI.
- **Multi-owner desde Fase 1**: recomiendo sí, aunque ahora sólo te uses tú. Cuesta una FK más y te ahorra una migración fea cuando aparezca el segundo titular.
- **Renombrar carpeta** `rental state` → `real estate` o `rental-management`: hacerlo antes de iniciar Fase 0.

---

## 5. Resumen ejecutivo

- **Mantén**: la metodología por fases con stop-points y la centralidad de `Lease`/`RentCondition`.
- **Cambia**: stack a SQLite + APScheduler (Docker opcional); fiscalidad a `TaxProfile` por lease; añade `Owner`, `Deposit`, `Expense`, `IndexUpdate`, `Document`; adelanta el PDF tras facturación; mejora conciliación con score+ventana; añade tests, backups y auditoría desde el principio.
- **Riesgo principal del plan original**: si lo ejecutas tal cual, las primeras facturas reales saldrán **fiscalmente incorrectas** (locales sin IVA) y tendrás que reescribir el módulo de facturación.
