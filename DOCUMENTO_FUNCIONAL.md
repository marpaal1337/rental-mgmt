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
- **Fase 4**: Generación de PDF de facturas
- **Fase 5**: Registro de pagos
- **Fase 6**: Gastos del inmueble
- **Fase 7**: Conciliación bancaria (importar CSV)
- **Fase 8**: API REST completa con endpoints CRUD
- **Fase 9**: Automatización (facturación mensual automática, detección de impagos)
- **Fase 10**: Backups, auditoría, UI opcional
