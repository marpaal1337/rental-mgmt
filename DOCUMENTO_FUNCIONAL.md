# Documento Funcional — rental-mgmt

## 1. Propósito del sistema

Sistema de gestión inmobiliaria para **single-user en España**, 100 % local/open source.
Permite gestionar contratos de alquiler, calcular rentas, aplicar revisiones IPC,
facturar con IVA/IRPF correcto, generar PDFs, registrar pagos, gastos,
conciliar movimientos bancarios, y automatizar tareas mensuales.

> **Estado actual**: Fases 0–11 completadas. Fase 12 en curso — 12.1 (factura legal:
> numeración, vencimiento, snapshot fiscal y rectificativas) completada.

---

## 2. Arquitectura general

| Capa | Tecnología |
|---|---|
| Backend API | FastAPI (Python 3.11+), rutas bajo `/api` |
| Frontend SPA | Vite + React 19 + TypeScript + Ant Design + TanStack Query |
| Base de datos | SQLite (WAL, claves foráneas activas) con SQLModel + Alembic |
| Autenticación | API Key via header `X-API-Key` |
| PDF | ReportLab (salida en `DATA_ROOT/data/invoices`) |
| Background jobs | APScheduler (auto-facturación mensual, backups) + catch-up al arrancar |
| Escritorio | pywebview sobre el mismo FastAPI local |
| Empaquetado | PyInstaller (onedir autocontenido) + InnoSetup |

---

## 3. Entidades del dominio

### 3.1 Owner (Propietario/Arrendador)

Persona física o sociedad que posee inmuebles. Un Owner puede tener varios Properties
y aparecer como arrendador en múltiples Leases.

**Campos**: nombre, tipo de documento (DNI/NIE/CIF), número, email, teléfono, dirección, IBAN de cobro.

**API**: `GET/POST /owners`, `GET/PUT /owners/{id}`

### 3.2 Property (Inmueble)

Edificio o finca registral. Contiene datos catastrales y de localización.

**Campos**: nombre, dirección, ciudad, provincia, código postal, referencia catastral.

Relación: un Property pertenece a un Owner, y contiene varios Units.

**API**: `GET/POST /properties`, `GET/PUT /properties/{id}`

### 3.3 Unit (Unidad alquilable)

Unidad dentro de un inmueble que se alquila de forma independiente
(ej: "Piso 3º A", "Local Comercial Bajo").

**Campos**: nombre, tipo (vivienda / local / garaje / trastero), superficie en m², activo.

Relación: un Unit pertenece a un Property, y tiene varios Leases (históricos).

**API**: `GET/POST /units`, `GET/PUT /units/{id}`

### 3.4 Tenant (Inquilino)

Persona física o jurídica que alquila una unidad.

**Campos**: nombre, tipo de documento, número, email, teléfono, dirección.

**API**: `GET/POST /tenants`, `GET/PUT /tenants/{id}`

### 3.5 Lease (Contrato de alquiler)

Entidad central del sistema. Vincula una Unit con un Tenant y un Owner
durante un periodo temporal.

**Campos**: fechas inicio/fin, activo, notas.

Relaciones:
- Tiene un **TaxProfile** (fiscalidad: IVA/IRPF)
- Tiene un **Deposit** (fianza)
- Tiene un histórico de **RentConditions** (rentas)
- Tiene un histórico de **IndexUpdates** (revisiones IPC/IRAV)

**API**: `GET/POST /leases`, `GET/PUT /leases/{id}`

### 3.6 RentCondition (Condición de renta)

Registro histórico del importe de renta vigente desde una fecha concreta.
Cada vez que cambia la renta (por revisión IPC, acuerdo, etc.) se crea
una nueva RentCondition, manteniendo el histórico.

**Campos**: fecha de inicio, renta mensual (base imponible), notas.

**API**: `GET/POST /leases/{id}/rent-conditions`

### 3.7 TaxProfile (Perfil fiscal)

Configuración fiscal de un contrato. Nunca se hardcodean tipos impositivos
— cada Lease tiene su propio TaxProfile.

**Campos**: tipo IVA (0 % vivienda, 21 % local), tipo IRPF retención (0 % o 19 %),
exento de IVA (sí/no), aplica retención (sí/no).

**API**: `GET /leases/{id}/tax-profile`, `PUT /leases/{id}/tax-profile`

### 3.8 Deposit (Fianza)

Depósito obligatorio en organismo autonómico (IVIMA, INCASOL, etc.).

**Campos**: importe, fecha de depósito, organismo, fecha de devolución.

**API**: `GET /leases/{id}/deposit`, `PUT /leases/{id}/deposit`

### 3.9 IndexUpdate (Revisión IPC/IRAV)

Registro de cada revisión de renta por índice. Se almacena la renta anterior,
la nueva, el tipo de índice y su valor, y la fecha de aplicación.

**Campos**: fecha de aplicación, renta anterior, renta nueva, tipo de índice, valor del índice.

**API**: `GET /leases/{id}/index-updates`

### 3.10 Invoice (Factura)

Factura mensual generada automáticamente para un contrato. Refleja el periodo,
los importes calculados con IVA/IRPF según el perfil fiscal del contrato,
y el estado (borrador/emitida/cobrada/cancelada).

**Campos**: periodo (YYYY-MM), fecha de emisión, fecha de vencimiento, estado,
base imponible total, cuota IVA total, retención IRPF total, importe total.

**Numeración legal**: cada factura recibe al emitirse un **número correlativo
persistido** por serie y ejercicio (`A-2026-0001`), sin huecos y sin reutilizar
números de facturas anuladas. Las rectificativas usan serie propia (`R-...`).

**Snapshot fiscal**: al generar la factura se congelan nombre, documento y
dirección del arrendador y del arrendatario, de modo que cambios posteriores en
las fichas no alteran facturas ya emitidas.

**Rectificativas**: una factura emitida puede rectificarse (totalmente) creando
una factura con importes negados enlazada a la original, con motivo obligatorio.
La original se conserva (nunca se borra) y solo puede rectificarse una vez.

**API**: `GET/POST /invoices`, `GET /invoices/{id}`, `POST /invoices/generate`,
`POST /invoices/{id}/rectify`, `GET /invoices/{id}/pdf`

### 3.11 InvoiceLine (Línea de factura)

Cada línea detalla un concepto de la factura: base imponible, tipo de IVA,
cuota IVA, tipo de IRPF y retención aplicada.

**Campos**: concepto, base imponible, tipo IVA, cuota IVA, tipo IRPF, retención IRPF.

### 3.12 Payment (Pago)

Registro de pago vinculado a una factura.

**API**: `GET /payments`, `POST /payments`

### 3.13 Expense (Gasto)

Gasto asociado a un Property (comunidad, reparaciones, suministros, IBI, etc.).

**Categorías**: community, repairs, supplies, taxes, insurance, admin_fees, other.

**API**: `GET/POST /expenses`, `GET /expenses/categories`, `GET /expenses/summary`

### 3.14 BankMovement (Movimiento bancario)

Movimiento importado de CSV bancario para conciliación. Estados: unmatched, proposed, confirmed.

**API**: `POST /reconciliation/import`, `GET /reconciliation/movements`, `GET /reconciliation/unmatched`, `GET /reconciliation/proposed`

### 3.15 Reconciliation (Conciliación)

Emparejamiento propuesto entre BankMovement y Payment.

**API**: `POST /reconciliation/{id}/propose`, `POST /reconciliation/confirm/{id}`

---

## 4. Servicios disponibles

### 4.1 LeaseService.get_active_rent(lease_id, date) → renta mensual

Dado un contrato y una fecha, devuelve la renta mensual vigente en esa fecha.
Busca la RentCondition más reciente cuya fecha de inicio sea anterior o igual
a la fecha indicada.

**Si no hay condición aplicable**: lanza `NoActiveRentError`.

### 4.2 IndexUpdateService.apply_index(lease_id, rate, date, index_name)

Aplica una revisión de renta por índice (IPC, IRAV, IGC).

1. Valida el índice (debe ser > −100 % y ≤ 50 %) y que no exista ya una
   revisión para ese contrato y fecha
2. Obtiene la renta vigente en la fecha indicada
3. Calcula la nueva renta: `anterior × (1 + rate)`
4. Crea una nueva **RentCondition** con la renta actualizada desde esa fecha
5. Crea un registro **IndexUpdate** con todos los datos de la revisión

### 4.3 InvoiceService.generate_monthly(period)

Genera facturas para todos los contratos activos en un periodo mensual dado
(validado `YYYY-MM`). Es **idempotente**: si ya existe factura activa para ese
lease y periodo, la salta (garantizado también por índice único en base de datos).

Las facturas nacen en estado **issued** (emitida), con número legal asignado,
fecha de vencimiento (emisión + 30 días por defecto) y snapshot fiscal de las
partes. Los contratos sin `TaxProfile` o sin condición de renta se omiten y se
registran en el log, sin abortar el lote.

### 4.3b InvoiceService.rectify(invoice_id, reason)

Crea una factura rectificativa con los importes negados, en serie `R`, vinculada
a la factura original mediante `corrected_invoice_id` y con motivo obligatorio.
Rechaza rectificar dos veces la misma factura y rectificar una rectificativa.
La factura original nunca se modifica ni se elimina.

### 4.4 PDFService.render_invoice(invoice_id)

Convierte una factura en un PDF listo para enviar al inquilino usando ReportLab.
Almacena el PDF en `DATA_ROOT/data/invoices/{año}/{mes}/{invoice_id}.pdf`.

### 4.5 PaymentService.register(invoice_id, amount, date)

Registra un pago sobre una factura y actualiza su estado automáticamente
(issued → partial → paid según el total pagado). **Rechaza sobrepagos** que
superen el saldo pendiente y **recalcula el estado** al editar o eliminar un pago.

### 4.6 ExpenseService

Registra gastos del inmueble y ofrece resumen de rentabilidad neta:
ingresos del año (solo facturas emitidas, parciales o pagadas; excluye
borradores y anuladas) vs gastos totales, rentabilidad neta y desglose por
categoría.

### 4.7 ReconciliationService

Importa movimientos bancarios desde CSV (adaptadores ING y genérico),
**deduplica** movimientos repetidos, propone coincidencias con pagos mediante
score (importe exacto, fecha ±5 días, coincidencia de concepto/inquilino e IBAN
recurrente) y permite confirmar/rechazar manualmente. Se pueden proponer varios
candidatos por movimiento; al confirmar uno, el resto se descartan.
**Nunca se auto-confirma** una coincidencia.

### 4.8 BackupService

Copia automática de `rental.db` con la API de backup de SQLite (segura con WAL),
verificación `integrity_check` y retención de 7 días. Se ejecuta vía APScheduler
a las 5:00 y también antes de cada migración al arrancar el escritorio.

### 4.9 InvoiceNumberingService

Asigna números correlativos por serie y ejercicio (`A-2026-0001`) de forma
transaccional, con reintento ante colisión y sin reutilizar números de facturas
eliminadas. Las rectificativas usan la serie `R`. El número se persiste en la
factura y el PDF lo muestra tal cual.

---

## 5. Frontend — Interfaz de usuario (React SPA)

### 5.1 Pantallas principales

| Pantalla | Ruta | Descripción |
|---|---|---|
| Dashboard | `/` | Resumen: contratos activos, facturas del mes, pagos, gastos del año |
| Contratos | `/leases` | Lista de contratos con filtros y acciones |
| Contrato detalle | `/leases/:id` | Tabs: Renta (historial + crear), Fiscal (IVA/IRPF), Fianza, IPC (aplicar índice + historial) |
| Facturas | `/invoices` | Lista con nº legal, vencimiento y descarga PDF; detalle con líneas y acción **Rectificar** |
| Pagos | `/payments` | Lista de pagos registrados, formulario para nuevo pago |
| Gastos | `/expenses` | Lista de gastos, selector de año + botón "Resumen" con tarjetas de rentabilidad |
| Conciliación | `/reconciliation` | 3 tabs: Importar CSV (drag-and-drop), Sin procesar (propuesta + modal con score), Todos |
| Propietarios | `/owners` | CRUD: tabla + modal de formulario |
| Inquilinos | `/tenants` | CRUD: tabla + modal de formulario |
| Propiedades | `/properties` | CRUD: tabla + modal de formulario |
| Unidades | `/units` | CRUD: tabla + modal de formulario |

### 5.2 Componentes reutilizables

- AppLayout: sidebar con menú, header, contenido
- CrudPage: shell genérico de listado + modal + edición (Owners, Tenants, Properties, Units, Leases, Payments)
- LeaseForm, PaymentForm, ExpenseForm, OwnerForm, PropertyForm, UnitForm, TenantForm: modales de formulario
- Carga diferida (React.lazy + Suspense) en todas las rutas
- `utils/labels.ts`: etiquetas y colores compartidos (estados, métodos, categorías)

### 5.3 Funcionalidades clave

- **TanStack Query**: caché, invalidación y estados de carga/error únicos para toda la app
- **Manejo de errores**: interceptor Axios que extrae el `detail` de FastAPI y lo muestra al usuario
- **Blob URL management**: descarga de PDF con auto-revocación
- **ErrorBoundary**: captura errores de renderizado en cada página
- **Empty states**: tablas con mensaje personalizado "No hay datos"
- **Aria-labels**: accesibilidad en todos los icon buttons
- **Ant Design ConfigProvider**: locale en español
- **TypeScript estricto** y ESLint sin errores

---

## 6. API completa

Todos los endpoints viven bajo el prefijo `/api` (ej. `/api/leases`) y requieren
header `X-API-Key`. La raíz `/` sirve la SPA y `/health` está fuera del prefijo.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/leases` | Listar contratos |
| GET | `/leases/{id}` | Obtener contrato |
| POST | `/leases` | Crear contrato |
| PUT | `/leases/{id}` | Actualizar contrato |
| GET | `/leases/{id}/rent` | Renta vigente |
| GET | `/leases/{id}/rent-conditions` | Histórico rentas |
| POST | `/leases/{id}/rent-conditions` | Crear condición de renta |
| GET | `/leases/{id}/tax-profile` | Perfil fiscal |
| PUT | `/leases/{id}/tax-profile` | Crear/actualizar perfil fiscal |
| GET | `/leases/{id}/deposit` | Fianza |
| PUT | `/leases/{id}/deposit` | Crear/actualizar fianza |
| GET | `/leases/{id}/index-updates` | Histórico revisiones IPC |
| POST | `/leases/{id}/apply-index` | Aplicar revisión IPC |
| DELETE | `/leases/{id}` | Baja lógica del contrato |
| GET | `/invoices` | Listar facturas |
| GET | `/invoices/{id}` | Obtener factura |
| POST | `/invoices/generate` | Generar facturas mensuales (con numeración legal) |
| POST | `/invoices/{id}/rectify` | Crear factura rectificativa |
| GET | `/invoices/{id}/pdf` | Descargar PDF |
| GET | `/payments` | Listar pagos |
| POST | `/payments` | Registrar pago |
| PUT | `/payments/{id}` | Actualizar pago (recalcula factura) |
| DELETE | `/payments/{id}` | Baja lógica del pago (recalcula factura) |
| GET | `/expenses` | Listar gastos (filtro opcional `property_id` y `year`) |
| POST | `/expenses` | Registrar gasto |
| PUT | `/expenses/{id}` | Actualizar gasto |
| DELETE | `/expenses/{id}` | Baja lógica del gasto |
| GET | `/expenses/categories` | Categorías disponibles |
| GET | `/expenses/summary` | Resumen rentabilidad |
| GET | `/owners` | Listar propietarios |
| POST | `/owners` | Crear propietario |
| GET | `/owners/{id}` | Obtener propietario |
| PUT | `/owners/{id}` | Actualizar propietario |
| DELETE | `/owners/{id}` | Baja lógica del propietario |
| GET | `/tenants` | Listar inquilinos |
| POST | `/tenants` | Crear inquilino |
| GET | `/tenants/{id}` | Obtener inquilino |
| PUT | `/tenants/{id}` | Actualizar inquilino |
| DELETE | `/tenants/{id}` | Baja lógica del inquilino |
| GET | `/properties` | Listar inmuebles |
| POST | `/properties` | Crear inmueble |
| GET | `/properties/{id}` | Obtener inmueble |
| PUT | `/properties/{id}` | Actualizar inmueble |
| DELETE | `/properties/{id}` | Baja lógica del inmueble |
| GET | `/units` | Listar unidades |
| POST | `/units` | Crear unidad |
| GET | `/units/{id}` | Obtener unidad |
| PUT | `/units/{id}` | Actualizar unidad |
| DELETE | `/units/{id}` | Baja lógica de la unidad |
| POST | `/reconciliation/import` | Importar CSV bancario |
| POST | `/reconciliation/{id}/propose` | Proponer coincidencias |
| POST | `/reconciliation/confirm/{id}` | Confirmar conciliación |
| GET | `/reconciliation/unmatched` | Movimientos sin conciliar |
| GET | `/reconciliation/proposed` | Movimientos propuestos |
| GET | `/reconciliation/movements` | Todos los movimientos |
| GET | `/stats` | Estadísticas del dashboard |
| GET | `/health` | Health check |

---

## 7. Tutorial de uso de la aplicación

Este tutorial guía al usuario desde cero: arrancar el sistema, cargar datos de prueba, y
realizar las operaciones diarias más comunes.

---

### 7.1 Primer arranque

```bash
# 1. Aplicar migraciones
alembic upgrade head

# 2. (Opcional) Cargar datos de semilla para explorar
python scripts/seed.py

# 3. Arrancar backend (terminal 1)
uvicorn app.main:app --reload

# 4. Arrancar frontend (terminal 2)
cd frontend && npm run dev
```

Abrir `http://localhost:5173` en el navegador. La API key por defecto
(`dev-key-123`) ya está configurada en el frontend.

En modo escritorio, `python -m desktop` arranca migraciones, catch-up de jobs y
ventana nativa. Una instalación nueva arranca **sin datos**; para cargar la
semilla de demostración hay que definir `RENTAL_MGMT_DEMO=1`.

---

### 7.2 Flujo completo: alta de un nuevo contrato

Paso a paso desde cero, sin usar la semilla:

**Paso 1 — Crear propietario**

1. Ir a **Maestros → Propietarios**
2. Clic en **"Nuevo propietario"**
3. Rellenar: nombre, DNI/NIE/CIF, email, teléfono
4. Clic en **Guardar**

**Paso 2 — Crear inquilino**

1. Ir a **Maestros → Inquilinos**
2. Clic en **"Nuevo inquilino"**
3. Rellenar datos y guardar

**Paso 3 — Crear propiedad e inmueble**

1. Ir a **Maestros → Propiedades**
2. Clic en **"Nueva propiedad"**: nombre, dirección, propietario (seleccionar el creado antes)
3. Guardar
4. Ir a **Maestros → Unidades**
5. Clic en **"Nueva unidad"**: nombre (ej. "Piso 1º"), tipo (vivienda/local/garaje),
   propiedad (seleccionar la creada antes). Guardar

**Paso 4 — Crear contrato**

1. Ir a **Contratos**, clic en **"Nuevo contrato"**
2. Seleccionar unidad, inquilino, propietario, fecha de inicio
3. Guardar

**Paso 5 — Configurar renta y fiscalidad**

Una vez creado el contrato, clic en su fila para ver el detalle:

1. **Pestaña Renta**: clic en **"Nueva condición"**. Introducir fecha de inicio
   y renta mensual (ej. 850,00 €). Guardar.
2. **Pestaña Fiscal**: rellenar IVA (0 % para vivienda, 21 % para local) e
   IRPF (0 % o 19 %). Guardar.
3. **Pestaña Fianza**: introducir importe (1 mes de renta), fecha de depósito
   y organismo autonómico (IVIMA, INCASOL, etc.). Guardar.

**Paso 6 — Generar facturas**

1. Ir a **Facturas**
2. Clic en **"Generar facturas del mes"**
3. Introducir período (ej. `2026-06`) y clic en **Generar**
4. Aparecerán las facturas creadas, cada una con su **número legal** (ej.
   `A-2026-0001`) y su **fecha de vencimiento**. Clic en una fila para ver su
   detalle (líneas con desglose de IVA/IRPF)
5. Clic en el icono PDF para descargar la factura en PDF

**Paso 6b — Rectificar una factura**

Si una factura ya emitida contiene un error:

1. Ir a **Facturas** y clic en la factura a rectificar
2. En el detalle, clic en **"Rectificar"**
3. Escribir el **motivo** (obligatorio) y confirmar
4. El sistema crea una **factura rectificativa** en serie `R` con los importes
   negados, enlazada a la original. La original se conserva y no puede
   rectificarse dos veces

**Paso 7 — Registrar pago**

1. Ir a **Pagos**
2. Clic en **"Nuevo pago"**
3. Seleccionar la factura, importe, fecha, método (transferencia/efectivo/bizum/...)
4. Guardar. El estado de la factura se actualizará automáticamente a `paid`

---

### 7.3 Revisión IPC anual

Cuando toque actualizar la renta según el IPC:

1. Ir a **Contratos**, clic en el contrato deseado
2. **Pestaña IPC**
3. Clic en **"Aplicar índice"**
4. Introducir:
   - **Fecha de aplicación**: fecha desde la que aplica la nueva renta
   - **Índice**: valor decimal (ej. 0,03 para un 3 %)
   - **Nombre del índice**: IPC, IRAV, IGC, etc.
   - **Notas**: opcional
5. Clic en **Aplicar**. El sistema:
   - Crea una nueva RentCondition con la renta incrementada
   - Registra el IndexUpdate en el histórico
   - La renta vigente se actualiza automáticamente para futuras facturas
6. La nueva renta aparecerá en el histórico de la pestaña **Renta**

---

### 7.4 Registrar gastos y ver rentabilidad

1. Ir a **Gastos**
2. Clic en **"Nuevo gasto"**
3. Seleccionar propiedad, categoría, importe, fecha, proveedor
4. Marcar **"Deducible"** si aplica (gastos de comunidad, reparaciones, etc.)
5. Guardar
6. Para ver el resumen anual: seleccionar año y clic en **"Resumen"**
7. Aparecen tarjetas con:
   - **Ingresos totales** (suma de rentas del año)
   - **Gastos totales**
   - **Gastos deducibles**
   - **Rentabilidad neta** (ingresos − gastos)
   - Desglose por categoría (comunidad, reparaciones, IBI, etc.)

---

### 7.5 Conciliación bancaria

Cuando se recibe la transferencia del inquilino:

**Opción A — Importar CSV**

1. Ir a **Conciliación → Importar CSV**
2. Arrastrar el extracto bancario (formato CSV)
3. Los movimientos aparecen en la pestaña **Sin procesar**

**Opción B — Movimientos pendientes**

1. Ir a **Conciliación → Sin procesar**
2. Cada movimiento tiene un botón **"Proponer"**
3. El sistema busca pagos con el mismo importe y fecha cercana, mostrando
   un score de coincidencia (0,0–1,0)
4. Revisar la propuesta y clic en **"Confirmar"** si es correcta
5. El movimiento pasa a estado `confirmed` y el pago queda conciliado

**Ver todos los movimientos**: pestaña **"Todos"** con el historial completo.

---

### 7.6 Automatización (sin intervención)

El sistema ejecuta tareas automáticas en segundo plano (requiere que el backend
esté corriendo 24/7):

| Tarea | Cuándo | Resultado |
|---|---|---|
| Facturación mensual | 1er día del mes 06:00 | Se crean facturas para todos los contratos activos |
| Backup diario | Cada día 05:00 | Copia de seguridad en `data/backups/` (retención 7 días) |
| Detección de impagos | 1er día del mes 07:00 | Registra alertas para facturas con >30 días sin pagar |

No requiere ninguna acción del usuario. Las facturas generadas aparecen
directamente en la pantalla **Facturas**.

---

### 7.7 Gestión de datos maestros

**Añadir/editar/ver** propietarios, inquilinos, propiedades y unidades
desde el submenú **Maestros** del sidebar.

Cada pantalla maestra ofrece:
- **Tabla** con todos los registros
- **Búsqueda** por nombre/documento
- **Crear**: modal con formulario completo
- **Editar**: clic en el icono de lápiz en la fila
- **Ver detalle**: clic en el icono de ojo

El formulario de **Propiedad** requiere seleccionar un propietario existente.
El formulario de **Unidad** requiere seleccionar una propiedad existente.

---

### 7.8 Dashboard

La pantalla de inicio (`/`) muestra un resumen visual:

- **Contratos activos**: número total de leases en vigor
- **Facturas este mes**: total facturado en el mes actual
- **Pagos este mes**: total cobrado en el mes actual
- **Gastos este año**: total gastado en el año actual
- Acceso rápido a las secciones principales

---

## 8. Automatización

| Tarea | Cuándo | Qué hace |
|---|---|---|
| Facturación mensual | 1er día de cada mes a las 06:00 | Genera facturas para leases activos |
| Backup automático | Cada día a las 05:00 | Copia `rental.db` en `data/backups/`, retención 7 días |
| Detección de impagos | Cada día a las 07:00 | Busca facturas sin pagar con más de 30 días de antigüedad y registra EventLog (una vez al día) |

**Catch-up**: al arrancar el escritorio se ejecutan facturación del mes en curso
y detección de impagos, de modo que un equipo apagado el día 1 no pierde la
automatización.

---

## 9. Datos de semilla

Ejecutar `python scripts/seed.py` (con `--clean` para reiniciar), o
`RENTAL_MGMT_DEMO=1` al arrancar el escritorio en una base vacía, crea:

| Entidad | Datos |
|---|---|
| Owner | Juan Pérez García (DNI), María López Ruiz (DNI) |
| Property | Edificio Centro, Chalet Norte |
| Unit | Piso 3º A (vivienda 85m²), Local Comercial (120m²), Garaje 7 (25m²) |
| Tenant | Ana Martínez López, Comercial Pérez SL |
| Lease | Vivienda habitual 850€/mes, Local 1500€/mes |
| RentCondition | 3 condiciones históricas (incluye IPC) |
| TaxProfile | IVA exento (vivienda), IVA 21% + IRPF 19% (local) |
| Deposit | Fianzas depositadas en IVIMA |
| IndexUpdate | 1 revisión IPC aplicada |
| Invoice | 6 facturas generadas (3 por lease) |
| Payment | 3 pagos registrados |
| Expense | 8 gastos variados |
| BankMovement | 3 movimientos sin conciliar |

---

## 10. Empaquetado e instalación

La aplicación se distribuye como aplicación de escritorio nativa para Windows
con una única vía: **PyInstaller (onedir autocontenido) + InnoSetup**. El
equipo destino no necesita Python instalado.

### 10.1 Script unificado
```bash
python scripts/build_windows_installer.py             # .exe InnoSetup + .zip
python scripts/build_windows_installer.py --innosetup # Solo .exe
python scripts/build_windows_installer.py --zip       # Solo .zip portable
python scripts/build_windows_installer.py --skip-frontend
```

Flujo: icono → `npm run build` → PyInstaller `rental-mgmt.spec` →
InnoSetup empaqueta `dist/rental-mgmt/`.

Los datos (`data/db`, `data/backups`, `data/invoices`) se conservan al
desinstalar (`uninsneveruninstall`).

---

## 11. Fases completadas

- ✅ **Fase 0**: Bootstrap (FastAPI, pytest, ruff, estructura)
- ✅ **Fase 1**: Modelos core (Owner, Property, Unit, Tenant, Lease, RentCondition, TaxProfile, Deposit)
- ✅ **Fase 2**: LeaseService + IndexUpdateService (renta vigente, revisiones IPC)
- ✅ **Fase 3**: Facturación mensual con IVA/IRPF (Invoice, InvoiceLine, InvoiceService)
- ✅ **Fase 4**: PDF de factura (PDFService.render_invoice)
- ✅ **Fase 5**: Pagos (Payment, PaymentService)
- ✅ **Fase 6**: Gastos (Expense, ExpenseService)
- ✅ **Fase 7**: Conciliación bancaria (BankMovement, Reconciliation, ReconciliationService)
- ✅ **Fase 8**: API REST completa (50+ endpoints) + frontend React SPA
- ✅ **Fase 9**: Automatización (APScheduler, facturación mensual, backups, impagos)
- ✅ **Fase 10**: Calidad (backups automáticos, soft-delete audit en todos los servicios, frontend con todas las páginas CRUD)
- ✅ **Fase 11**: Consolidación — integridad SQLite (WAL real, claves foráneas, índices, unicidad de facturas), corrección de bugs de dinero (sobrepagos, estado de facturas, conciliación multi-candidato), API bajo `/api`, catch-up de jobs, backup con `integrity_check`, empaquetado único PyInstaller + InnoSetup, frontend con TanStack Query y TypeScript estricto, 147 tests con cobertura mínima del 80 % en servicios
- 🔄 **Fase 12** (en curso) — Fiscal/CRM:
  - ✅ **12.1 Factura legal**: numeración correlativa por serie y ejercicio, fecha de vencimiento, snapshot fiscal emisor/receptor, rectificativas con serie `R`, IBAN de cobro en propietarios, dirección en inquilinos; 172 tests
  - ⏳ **12.2 Informes fiscales** (303/190/100)
  - ⏳ **12.3 Avisos de impago y actividad** (job sobre vencimiento, API de eventos)
  - ⏳ **12.4 Plazos de fianza** (estado, justificante, alertas)
