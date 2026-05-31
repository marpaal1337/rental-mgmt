# Documento Funcional — rental-mgmt

## 1. Propósito del sistema

Sistema de gestión inmobiliaria para **single-user en España**, 100 % local/open source.
Permite gestionar contratos de alquiler, calcular rentas, aplicar revisiones IPC/IRAV,
y (en fases futuras) facturar con IVA/IRPF correcto, generar PDFs, registrar pagos,
conciliar movimientos bancarios, y automatizar tareas mensuales.

> **Estado actual**: Fase 2 completada — modelo de datos + servicios de renta.

---

## 2. Entidades del dominio

### 2.1 Owner (Propietario/Arrendador)

Persona física o sociedad que posee inmuebles. Un Owner puede tener varios Properties
y aparecer como arrendador en múltiples Leases.

**Campos**: nombre, tipo de documento (DNI/NIE/CIF), número, email, teléfono, dirección.

### 2.2 Property (Inmueble)

Edificio o finca registral. Contiene datos catastrales y de localización.

**Campos**: nombre, dirección, ciudad, provincia, código postal, referencia catastral.

Relación: un Property pertenece a un Owner, y contiene varios Units.

### 2.3 Unit (Unidad alquilable)

Unidad dentro de un inmueble que se alquila de forma independiente
(ej: "Piso 3º A", "Local Comercial Bajo").

**Campos**: nombre, tipo (vivienda / local / garaje / trastero), superficie en m², activo.

Relación: un Unit pertenece a un Property, y tiene varios Leases (históricos).

### 2.4 Tenant (Inquilino)

Persona física o jurídica que alquila una unidad.

**Campos**: nombre, tipo de documento, número, email, teléfono.

### 2.5 Lease (Contrato de alquiler)

Entidad central del sistema. Vincula una Unit con un Tenant y un Owner
durante un periodo temporal.

**Campos**: fechas inicio/fin, activo, notas.

Relaciones:
- Tiene un **TaxProfile** (fiscalidad: IVA/IRPF)
- Tiene un **Deposit** (fianza)
- Tiene un histórico de **RentConditions** (rentas)
- Tiene un histórico de **IndexUpdates** (revisiones IPC/IRAV)

### 2.6 RentCondition (Condición de renta)

Registro histórico del importe de renta vigente desde una fecha concreta.
Cada vez que cambia la renta (por revisión IPC, acuerdo, etc.) se crea
una nueva RentCondition, manteniendo el histórico.

**Campos**: fecha de inicio, renta mensual (base imponible), notas.

### 2.7 TaxProfile (Perfil fiscal)

Configuración fiscal de un contrato. Nunca se hardcodean tipos impositivos
— cada Lease tiene su propio TaxProfile.

**Campos**: tipo IVA (0 % vivienda, 21 % local), tipo IRPF retención (0 % o 19 %),
exento de IVA (sí/no), aplica retención (sí/no).

### 2.8 Deposit (Fianza)

Depósito obligatorio en organismo autonómico (IVIMA, INCASOL, etc.).

**Campos**: importe, fecha de depósito, organismo, fecha de devolución.

### 2.9 IndexUpdate (Revisión IPC/IRAV)

Registro de cada revisión de renta por índice. Se almacena la renta anterior,
la nueva, el tipo de índice y su valor, y la fecha de aplicación.

**Campos**: fecha de aplicación, renta anterior, renta nueva, tipo de índice, valor del índice.

### 2.10 Invoice (Factura)

Factura mensual generada automáticamente para un contrato. Refleja el periodo,
los importes calculados con IVA/IRPF según el perfil fiscal del contrato,
y el estado (borrador/emitida/cobrada/cancelada).

**Campos**: periodo (YYYY-MM), fecha de emisión, estado, base imponible total,
cuota IVA total, retención IRPF total, importe total.

### 2.11 InvoiceLine (Línea de factura)

Cada línea detalla un concepto de la factura: base imponible, tipo de IVA,
cuota IVA, tipo de IRPF y retención aplicada.

**Campos**: concepto, base imponible, tipo IVA, cuota IVA, tipo IRPF, retención IRPF.

---

## 3. Servicios disponibles

### 3.1 LeaseService.get_active_rent(lease_id, date) → renta mensual

Dado un contrato y una fecha, devuelve la renta mensual vigente en esa fecha.
Busca la RentCondition más reciente cuya fecha de inicio sea anterior o igual
a la fecha indicada.

**Casos de uso**:
- Calcular cuánto cobrar este mes
- Saber la renta histórica en una fecha pasada (para reclamaciones)
- Preparar datos para generar una factura

**Si no hay condición aplicable**: lanza `NoActiveRentError`.

### 3.2 IndexUpdateService.apply_index(lease_id, rate, date, index_name)

Aplica una revisión de renta por índice (IPC, IRAV, IGC).

**Qué hace**:
1. Obtiene la renta vigente en la fecha indicada
2. Calcula la nueva renta: `anterior × (1 + rate)`
3. Crea una nueva **RentCondition** con la renta actualizada desde esa fecha
4. Crea un registro **IndexUpdate** con todos los datos de la revisión

**Ejemplo**: IPC del 2 % el 1 de enero de 2025 sobre una renta de 1000 €
→ nueva renta de 1020 €, registro de revisión guardado.

### 3.3 InvoiceService.generate_monthly(period)

Genera facturas para todos los contratos activos en un periodo mensual dado.

**Qué hace**:
1. Busca todos los leases activos
2. Por cada lease, comprueba si ya existe factura para ese periodo (idempotente)
3. Obtiene la renta vigente y el perfil fiscal del contrato
4. Calcula IVA (si aplica) y retención IRPF (si aplica)
5. Crea una factura con una línea de detalle

**Casos de uso**:
- Generar todas las facturas del mes de junio 2026 de una sola vez
- Regenerar facturas de un periodo concreto

**Idempotente**: si ya existe una factura para ese lease y periodo, la salta.

**Si no hay perfil fiscal**: lanza `InvoiceGenerationError`.

**Ejemplos**:

| Tipo | Renta | IVA | IRPF | Total factura |
|---|---|---|---|---|
| Vivienda | 850,00 € | 0,00 € (exento) | 0,00 € | **850,00 €** |
| Local | 1.500,00 € | 315,00 € (21 %) | 285,00 € (19 %) | **1.530,00 €** |

### 3.4 PDFService.render_invoice(invoice_id)

Convierte una factura en un PDF listo para enviar al inquilino.

**Qué hace**:
1. Lee la factura de la BD con todas sus relaciones (lease, owner, tenant, líneas)
2. Construye un PDF con formato profesional español usando ReportLab
3. Incluye: datos del arrendador, arrendatario, tabla de líneas, desglose fiscal, total
4. Almacena el PDF en `data/invoices/{año}/{mes}/{invoice_id}.pdf`

**Salida**: ruta al archivo PDF generado.

**Ejemplo de uso**:
```python
from sqlmodel import Session
from app.database import engine
from app.services.pdf_service import PDFService

with Session(engine) as session:
    pdf_path = PDFService.render_invoice(session, invoice_id=1)
    print(f"PDF generado en: {pdf_path}")
```

### 3.5 PaymentService.register(invoice_id, amount, date)

Registra un pago sobre una factura y actualiza su estado automáticamente.

**Qué hace**:
1. Verifica que la factura existe
2. Crea un registro de pago con importe, fecha y método
3. Recalcula el estado de la factura:
   - Si el total pagado ≥ total factura → estado `paid`
   - Si hay pagos parciales → estado `partial`
   - Si no hay pagos → estado `draft`

**Métodos de pago**: transferencia, efectivo, bizum, domiciliación, tarjeta, otros.

**Ejemplo**:
```python
from datetime import date
from decimal import Decimal
from sqlmodel import Session
from app.database import engine
from app.services.payment_service import PaymentService

with Session(engine) as session:
    pago = PaymentService.register(
        session=session,
        invoice_id=1,
        amount=Decimal("850.00"),
        payment_date=date.today(),
        method="transferencia",
    )
    print(f"Factura estado: {pago.invoice.status}")  # → "paid"
```

### 3.6 ExpenseService — Gestión de gastos

Registra gastos del inmueble y ofrece resumen de rentabilidad neta.

**Categorías disponibles**: community (comunidad), repairs (reparaciones), supplies (suministros), taxes (IBI/basuras), insurance (seguro), admin_fees (gastos de administración), other (otros).

**Register**:
```python
gasto = ExpenseService.register(
    session=session,
    property_id=1,
    category="community",
    amount=Decimal("85.50"),
    expense_date=date(2024, 6, 1),
    deductible=True,
    supplier="Comunidad Centro",
)
```

**Summary**: ingresos totales del año vs gastos totales, rentabilidad neta:
```python
resumen = ExpenseService.summary(session, property_id=1, year=2024)
# => {
#     "total_income": Decimal("10200.00"),
#     "total_expenses": Decimal("1026.00"),
#     "deductible_expenses": Decimal("996.00"),
#     "net_profitability": Decimal("9174.00"),
#     "by_category": {"community": Decimal("1026.00")}
# }
```

---

## 4. Datos de semilla

Al ejecutar `python -m app.seed` se crean:

| Entidad | Datos |
|---|---|
| Owner | Juan Pérez García (DNI) |
| Property | Edificio Centro (Madrid) |
| Unit vivienda | Piso 3º A, 85 m² |
| Unit local | Local Comercial Bajo, 120 m² |
| Tenant 1 | Ana Martínez López (persona física) |
| Tenant 2 | Comercial Pérez SL (sociedad) |
| Lease 1 | Vivienda habitual, 850 €/mes, IVA exento |
| Lease 2 | Local comercial, 1500 €/mes, IVA 21% + IRPF 19% |
| Deposits | Fianzas depositadas en IVIMA |

### 3.7 ReconciliationService — Conciliación bancaria

Importa movimientos bancarios desde CSV y los empareja con pagos registrados.

**Importar CSV**:
```python
from app.services.bank_adapter import INGBankAdapter
from app.services.reconciliation_service import ReconciliationService

adapter = INGBankAdapter()
movements = ReconciliationService.import_csv(session, "extracto.csv", adapter)
# → lista de BankMovement en estado "unmatched"
```

**Proponer coincidencias**: busca pagos con mismo importe y fecha cercana (±5 días):
```python
recs = ReconciliationService.propose_matches(session, movement_id=1)
# → lista de Reconciliation propuestas con score 0.0–1.0
```

**Confirmar una conciliación**:
```python
rec = ReconciliationService.confirm_match(session, reconciliation_id=1)
# → BankMovement pasa a "confirmed"
```

**Ver movimientos sin conciliar**:
```python
pendientes = ReconciliationService.list_unmatched(session)
```

Se incluye adaptador genérico configurable (`GenericBankAdapter`) y uno específico para ING (`INGBankAdapter`). El sistema nunca auto-confirma matches — siempre requiere revisión manual.

---

## 5. Cómo usar el sistema (hoy)

```bash
# Arrancar la API
uvicorn app.main:app --reload

# Endpoints disponibles
GET  /        → {"message": "Rental Management System API"}
GET  /health  → {"status": "ok"}

# Ejecutar semilla
python -m app.seed

# Migraciones
alembic upgrade head
alembic revision --autogenerate -m "descripción del cambio"

# Tests
pytest -v
```

---

## 6. Lo que viene (próximas fases)

- ✅ **Fase 3**: Facturación mensual con IVA/IRPF correcto (Invoice, InvoiceLine, InvoiceService)
- ✅ **Fase 4**: PDF de factura (PDFService.render_invoice)
- ✅ **Fase 5**: Pagos (Payment, PaymentService.register)
- ✅ **Fase 6**: Gastos (Expense, ExpenseService)
- ✅ **Fase 7**: Conciliación bancaria (BankMovement, Reconciliation, ReconciliationService)
- **Fase 8**: API REST completa con endpoints CRUD
- **Fase 9**: Automatización (facturación mensual automática, detección de impagos)
- **Fase 10**: Backups, auditoría, UI opcional
