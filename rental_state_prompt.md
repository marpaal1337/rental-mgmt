# 🏢 Sistema de Gestión Inmobiliaria (Local, OSS, Single User)

## 🎯 Objetivo general

Construir un sistema backend local para gestionar alquileres inmobiliarios (viviendas y locales), con:

- Contratos de alquiler
- Facturación mensual automática
- Gestión de cobros e impagos
- Conciliación bancaria básica
- Generación de documentos (PDF)
- Automatización futura basada en eventos

⚠️ IMPORTANTE:
Este proyecto se construirá en fases.  
NO generar todo el sistema de una vez.

---

# 🧠 Principios del proyecto

- Single user (uso local)
- 100% open source
- Docker obligatorio
- Arquitectura modular
- Sin microservicios
- Sin sobreingeniería
- Priorizar simplicidad funcional

---

# 🧱 Stack obligatorio

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLModel o SQLAlchemy
- Celery + Redis
- Jinja2 + WeasyPrint
- Docker Compose

---

# 🚀 METODOLOGÍA (MUY IMPORTANTE)

Trabajar en **fases secuenciales**.

👉 En cada fase:
- implementar solo lo necesario
- no anticipar fases futuras
- no diseñar cosas que no se usan todavía
- al final de cada fase, parar y esperar confirmación

---

# 🧩 FASE 1 — CORE MODELADO (OBLIGATORIA)

## Objetivo
Definir y persistir el modelo de datos mínimo funcional.

## Tareas

Implementar:

- Property
- Unit
- Tenant
- Lease
- RentCondition

## Reglas

- Lease es la entidad central del sistema
- RentCondition permite evolución de renta en el tiempo
- NO implementar facturación aún
- NO implementar pagos aún
- NO implementar API compleja aún

## Output esperado

- Modelos SQL funcionando
- Migraciones o creación de tablas
- Seed básico de ejemplo (1 property, 1 lease)

## STOP POINT

Después de esta fase:
👉 NO continuar sin confirmación del usuario

---

# 🧩 FASE 2 — LÓGICA DE CONTRATOS

## Objetivo
Permitir calcular la renta activa de un contrato.

## Tareas

Crear servicio:

### LeaseService
- obtener renta activa según fecha
- aplicar RentCondition vigente

## Reglas

- NO facturación aún
- SOLO lógica de contratos

## Output esperado

- función que dado un lease + fecha devuelve renta actual

## STOP POINT

Esperar confirmación

---

# 🧩 FASE 3 — FACTURACIÓN

## Objetivo
Generar facturas mensuales automáticamente.

## Tareas

Implementar:

### Invoice model
- periodo YYYY-MM
- lease_id
- impuestos (IVA / IRPF)

### InvoiceService
- generate_monthly_invoices(period)

## Reglas

- local = sin IVA
- local = IRPF opcional
- vivienda = sin impuestos complejos

## Output

- facturas generadas en DB
- sin PDF todavía

## STOP POINT

Esperar confirmación

---

# 🧩 FASE 4 — PAGOS

## Objetivo
Registrar pagos y marcar facturas como pagadas.

## Tareas

- Payment model
- PaymentService
- endpoint básico de registro

## Matching simple

- por invoice_id directo (no conciliación bancaria aún)

## Output

- facturas con estado pagado

## STOP POINT

Esperar confirmación

---

# 🧩 FASE 5 — CONCILIACIÓN BANCARIA BÁSICA

## Objetivo
Importar movimientos bancarios y hacer matching simple.

## Tareas

- BankMovement model
- CSV import
- matching por:
  - importe
  - concepto

- Reconciliation model

## Output

- conciliación básica funcional

## STOP POINT

Esperar confirmación

---

# 🧩 FASE 6 — API FASTAPI

## Objetivo
Exponer funcionalidad core.

## Endpoints mínimos

- /leases
- /invoices
- /invoices/generate
- /payments
- /reconciliation/import

## Reglas

- API fina (sin lógica compleja)
- lógica siempre en services

## STOP POINT

---

# 🧩 FASE 7 — PDF FACTURAS

## Objetivo
Generar documentos PDF.

## Tareas

- Jinja2 template factura
- WeasyPrint render

## Output

- PDF descargable o almacenado

---

# 🧩 FASE 8 — AUTOMATIZACIÓN

## Objetivo
Jobs automáticos.

## Tareas

- Celery setup
- job mensual:
  - generar facturas
- job diario:
  - detectar impagos

- Event table (simple log)

---

# ⚠️ REGLAS CRÍTICAS PARA CLAUDE

- NO diseñar todo desde el inicio
- NO crear microservicios
- NO añadir features no solicitadas
- NO implementar UI compleja
- SIEMPRE terminar cada fase y esperar

---

# 🎯 DEFINICIÓN DE ÉXITO

El sistema debe poder:

- crear contratos
- generar facturas mensuales
- registrar pagos
- conciliar movimientos bancarios
- exportar documentos

Todo funcionando localmente con Docker.

---

# 🧭 INSTRUCCIÓN FINAL

Empieza SOLO con FASE 1.  
Cuando termines, detente completamente.