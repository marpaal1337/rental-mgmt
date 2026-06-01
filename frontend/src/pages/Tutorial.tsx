import {
  AppstoreOutlined,
  BookOutlined,
  BulbOutlined,
  CheckCircleOutlined,
  CreditCardOutlined,
  DatabaseOutlined,
  DollarOutlined,
  FileAddOutlined,
  FileTextOutlined,
  HomeOutlined,
  KeyOutlined,
  LinkOutlined,
  NodeIndexOutlined,
  PlayCircleOutlined,
  PullRequestOutlined,
  RocketOutlined,
  SettingOutlined,
  TeamOutlined,
  ToolOutlined,
  UserAddOutlined,
} from '@ant-design/icons'
import { Card, Collapse, Divider, Steps, Tag, Typography } from 'antd'
import type { CollapseProps } from 'antd'
import { useNavigate } from 'react-router-dom'

const { Title, Text, Paragraph } = Typography

const sections: CollapseProps['items'] = [
  {
    key: '1',
    label: (
      <span style={{ fontSize: 16, fontWeight: 600 }}>
        <RocketOutlined style={{ marginRight: 10 }} />
        Primer arranque
      </span>
    ),
    children: (
      <div>
        <Paragraph>
          Sigue estos pasos para poner el sistema en marcha desde cero.
        </Paragraph>
        <Steps
          direction="vertical"
          size="small"
          current={-1}
          items={[
            {
              title: 'Aplicar migraciones',
              description: 'alembic upgrade head',
              status: 'process',
              icon: <SettingOutlined />,
            },
            {
              title: 'Cargar datos de prueba (opcional)',
              description: 'python scripts/seed.py',
              status: 'process',
              icon: <DatabaseOutlined />,
            },
            {
              title: 'Arrancar backend',
              description: 'uvicorn app.main:app --reload',
              status: 'process',
              icon: <PlayCircleOutlined />,
            },
            {
              title: 'Arrancar frontend',
              description: 'cd frontend && npm run dev',
              status: 'process',
              icon: <PullRequestOutlined />,
            },
          ]}
        />
        <Divider />
        <Tag icon={<BulbOutlined />} color="gold">
          La API key por defecto (dev-key-123) ya está configurada en el frontend.
        </Tag>
        <div style={{ marginTop: 12 }}>
          <Text type="secondary">
            Abre <a href="http://localhost:5173" target="_blank" rel="noreferrer">http://localhost:5173</a> en tu navegador.
          </Text>
        </div>
      </div>
    ),
  },
  {
    key: '2',
    label: (
      <span style={{ fontSize: 16, fontWeight: 600 }}>
        <UserAddOutlined style={{ marginRight: 10 }} />
        Alta de un nuevo contrato
      </span>
    ),
    children: (
      <div>
        <Paragraph>
          Crea un contrato desde cero con todos sus datos asociados.
        </Paragraph>
        <TimelineStep num={1} title="Crear propietario" target="/owners" linkText="Ir a Propietarios">
          Ve a <strong>Maestros → Propietarios</strong>, clic en <Tag>Nuevo propietario</Tag> y rellena nombre, documento y datos de contacto.
        </TimelineStep>
        <TimelineStep num={2} title="Crear inquilino" target="/tenants" linkText="Ir a Inquilinos">
          Ve a <strong>Maestros → Inquilinos</strong>, clic en <Tag>Nuevo inquilino</Tag> con sus datos personales.
        </TimelineStep>
        <TimelineStep num={3} title="Crear propiedad" target="/properties" linkText="Ir a Propiedades">
          Ve a <strong>Maestros → Propiedades</strong>, crea la propiedad seleccionando el propietario que diste de alta.
        </TimelineStep>
        <TimelineStep num={4} title="Crear unidad" target="/units" linkText="Ir a Unidades">
          Ve a <strong>Maestros → Unidades</strong>, crea la unidad (piso, local, garaje) asociada a la propiedad.
        </TimelineStep>
        <TimelineStep num={5} title="Crear contrato" target="/leases" linkText="Ir a Contratos">
          Ve a <strong>Contratos</strong>, clic en <Tag>Nuevo contrato</Tag>. Selecciona unidad, inquilino y propietario.
        </TimelineStep>
        <TimelineStep num={6} title="Configurar renta y fiscalidad" icon={<SettingOutlined />}>
          Haz clic en el contrato creado y usa las pestañas:
          <ul>
            <li><strong>Renta</strong> → fija la renta mensual y fecha de inicio</li>
            <li><strong>Fiscal</strong> → configura IVA (0% vivienda, 21% local) e IRPF</li>
            <li><strong>Fianza</strong> → introduce el depósito y organismo autonómico</li>
          </ul>
        </TimelineStep>
        <TimelineStep num={7} title="Generar factura" target="/invoices" linkText="Ir a Facturas" icon={<FileAddOutlined />}>
          Ve a <strong>Facturas</strong>, clic en <Tag>Generar facturas del mes</Tag>. Introduce el período y confirma.
        </TimelineStep>
        <TimelineStep num={8} title="Registrar pago" target="/payments" linkText="Ir a Pagos" icon={<CreditCardOutlined />}>
          Ve a <strong>Pagos</strong>, clic en <Tag>Nuevo pago</Tag>. Selecciona la factura, importe y método. El estado se actualiza automáticamente.
        </TimelineStep>
      </div>
    ),
  },
  {
    key: '3',
    label: (
      <span style={{ fontSize: 16, fontWeight: 600 }}>
        <NodeIndexOutlined style={{ marginRight: 10 }} />
        Revisión IPC anual
      </span>
    ),
    children: (
      <div>
        <Paragraph>
          Cuando toque actualizar la renta según el IPC, haz lo siguiente:
        </Paragraph>
        <Steps
          direction="vertical"
          size="small"
          current={-1}
          items={[
            {
              title: 'Abrir contrato',
              description: 'Ve a Contratos y haz clic en el contrato a actualizar',
              status: 'process',
            },
            {
              title: 'Ir a pestaña IPC',
              description: 'Dentro del detalle del contrato, abre la pestaña "IPC"',
              status: 'process',
            },
            {
              title: 'Aplicar índice',
              description: 'Introduce fecha de aplicación, índice (ej. 0.03 para 3%), nombre del índice (IPC, IRAV, IGC) y notas opcionales',
              status: 'process',
            },
            {
              title: 'Confirmar',
              description: 'El sistema crea una nueva renta y la registra en el histórico automáticamente.',
              status: 'process',
            },
          ]}
        />
        <Divider />
        <Tag icon={<CheckCircleOutlined />} color="success">
          La nueva renta se reflejará en todas las facturas futuras.
        </Tag>
      </div>
    ),
  },
  {
    key: '4',
    label: (
      <span style={{ fontSize: 16, fontWeight: 600 }}>
        <DollarOutlined style={{ marginRight: 10 }} />
        Gastos y rentabilidad
      </span>
    ),
    children: (
      <div>
        <Paragraph>
          Registra los gastos de tus propiedades y consulta la rentabilidad anual.
        </Paragraph>
        <TimelineStep num={1} title="Registrar un gasto" target="/expenses" linkText="Ir a Gastos">
          Ve a <strong>Gastos</strong>, clic en <Tag>Nuevo gasto</Tag>. Selecciona propiedad,
          categoría (comunidad, reparaciones, suministros, IBI, seguro…), importe, fecha
          y si es deducible.
        </TimelineStep>
        <TimelineStep num={2} title="Ver resumen anual">
          En la misma pantalla, elige un año y clic en <Tag>Resumen</Tag>.
          Aparecerán tarjetas con:
          <ul>
            <li>📈 <strong>Ingresos totales</strong> del año</li>
            <li>📉 <strong>Gastos totales</strong></li>
            <li>💰 <strong>Rentabilidad neta</strong> (ingresos − gastos)</li>
            <li>📊 Desglose por categoría</li>
          </ul>
        </TimelineStep>
      </div>
    ),
  },
  {
    key: '5',
    label: (
      <span style={{ fontSize: 16, fontWeight: 600 }}>
        <LinkOutlined style={{ marginRight: 10 }} />
        Conciliación bancaria
      </span>
    ),
    children: (
      <div>
        <Paragraph>
          Empareja los cobros bancarios con las facturas emitidas.
        </Paragraph>
        <Steps
          direction="vertical"
          size="small"
          current={-1}
          items={[
            {
              title: 'Importar CSV',
              description: 'Ve a Conciliación → Importar CSV y arrastra el extracto bancario',
              status: 'process',
              icon: <FileAddOutlined />,
            },
            {
              title: 'Revisar movimientos',
              description: 'Los movimientos aparecen en la pestaña "Sin procesar"',
              status: 'process',
              icon: <FileTextOutlined />,
            },
            {
              title: 'Proponer coincidencia',
              description: 'Clic en "Proponer" para buscar pagos con mismo importe y fecha cercana. El sistema muestra un score de 0.0 a 1.0',
              status: 'process',
              icon: <NodeIndexOutlined />,
            },
            {
              title: 'Confirmar',
              description: 'Revisa la propuesta y confírmala. El movimiento pasa a "confirmed" y el pago queda conciliado.',
              status: 'process',
              icon: <CheckCircleOutlined />,
            },
          ]}
        />
      </div>
    ),
  },
  {
    key: '6',
    label: (
      <span style={{ fontSize: 16, fontWeight: 600 }}>
        <ToolOutlined style={{ marginRight: 10 }} />
        Gestión de datos maestros
      </span>
    ),
    children: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <Paragraph>
          Desde el submenú <strong>Maestros</strong> del panel lateral puedes gestionar
          propietarios, inquilinos, propiedades y unidades.
        </Paragraph>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
          <Card size="small" style={{ borderLeft: '3px solid #1677ff' }}>
            <Text strong><UserAddOutlined /> Propietarios</Text>
            <Paragraph type="secondary" style={{ margin: '8px 0 0' }}>
              Crea y edita los propietarios de los inmuebles.
            </Paragraph>
          </Card>
          <Card size="small" style={{ borderLeft: '3px solid #52c41a' }}>
            <Text strong><TeamOutlined /> Inquilinos</Text>
            <Paragraph type="secondary" style={{ margin: '8px 0 0' }}>
              Personas físicas o jurídicas que alquilan.
            </Paragraph>
          </Card>
          <Card size="small" style={{ borderLeft: '3px solid #faad14' }}>
            <Text strong><HomeOutlined /> Propiedades</Text>
            <Paragraph type="secondary" style={{ margin: '8px 0 0' }}>
              Edificios con dirección y referencia catastral.
            </Paragraph>
          </Card>
          <Card size="small" style={{ borderLeft: '3px solid #ff4d4f' }}>
            <Text strong><AppstoreOutlined /> Unidades</Text>
            <Paragraph type="secondary" style={{ margin: '8px 0 0' }}>
              Pisos, locales o garajes dentro de una propiedad.
            </Paragraph>
          </Card>
        </div>
      </div>
    ),
  },
  {
    key: '7',
    label: (
      <span style={{ fontSize: 16, fontWeight: 600 }}>
        <KeyOutlined style={{ marginRight: 10 }} />
        Automatización
      </span>
    ),
    children: (
      <div>
        <Paragraph>
          El sistema ejecuta tareas automáticas en segundo plano (requiere el backend activo 24/7).
        </Paragraph>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Card size="small">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Tag color="blue">1er día 06:00</Tag>
              <div>
                <Text strong>Facturación mensual</Text>
                <br />
                <Text type="secondary">Genera facturas para todos los contratos activos automáticamente.</Text>
              </div>
            </div>
          </Card>
          <Card size="small">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Tag color="green">Cada día 05:00</Tag>
              <div>
                <Text strong>Backup automático</Text>
                <br />
                <Text type="secondary">Copia de seguridad de la base de datos en data/backups/ (retención 7 días).</Text>
              </div>
            </div>
          </Card>
          <Card size="small">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Tag color="red">1er día 07:00</Tag>
              <div>
                <Text strong>Detección de impagos</Text>
                <br />
                <Text type="secondary">Alerta sobre facturas con más de 30 días sin pagar.</Text>
              </div>
            </div>
          </Card>
        </div>
      </div>
    ),
  },
]

function TimelineStep({
  num,
  title,
  children,
  target,
  linkText,
  icon,
}: {
  num: number
  title: string
  children: React.ReactNode
  target?: string
  linkText?: string
  icon?: React.ReactNode
}) {
  const navigate = useNavigate()
  return (
    <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #1677ff, #4096ff)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontWeight: 700,
          fontSize: 14,
          flexShrink: 0,
          marginTop: 2,
        }}
      >
        {icon ?? num}
      </div>
      <div style={{ flex: 1 }}>
        <Text strong style={{ fontSize: 15, display: 'block', marginBottom: 4 }}>
          {title}
        </Text>
        <Paragraph style={{ margin: 0 }}>{children}</Paragraph>
        {target && linkText && (
          <Tag
            color="blue"
            style={{ cursor: 'pointer', marginTop: 8 }}
            onClick={() => navigate(target)}
          >
            {linkText} →
          </Tag>
        )}
      </div>
    </div>
  )
}

export default function Tutorial() {
  return (
    <div>
      <div
        style={{
          background: 'linear-gradient(135deg, #141414 0%, #1f1f1f 50%, #262626 100%)',
          margin: -24,
          padding: '48px 40px',
          marginBottom: 24,
        }}
      >
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              background: 'linear-gradient(135deg, #1677ff, #4096ff)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 20,
              boxShadow: '0 8px 24px rgba(22,119,255,0.35)',
            }}
          >
            <BookOutlined style={{ fontSize: 28, color: '#fff' }} />
          </div>
          <Title level={2} style={{ color: '#fff', margin: 0, fontWeight: 700 }}>
            Tutorial
          </Title>
          <Title level={5} style={{ color: 'rgba(255,255,255,0.65)', marginTop: 8, fontWeight: 400 }}>
            Aprende a usar rental-mgmt paso a paso
          </Title>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <Collapse
          accordion
          defaultActiveKey={['1']}
          items={sections}
          style={{
            background: '#fff',
            borderRadius: 8,
          }}
        />

        <Card
          style={{
            marginTop: 24,
            background: 'linear-gradient(135deg, #f6ffed, #d9f7be)',
            border: '1px solid #b7eb8f',
            borderRadius: 8,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
            <BulbOutlined style={{ fontSize: 24, color: '#52c41a', marginTop: 2 }} />
            <div>
              <Text strong style={{ fontSize: 15 }}>
          ¿Tienes más dudas?
              </Text>
              <Paragraph style={{ margin: '4px 0 0' }}>
                Consulta el archivo <Tag>DOCUMENTO_FUNCIONAL.md</Tag> para documentación
                detallada del sistema, incluyendo la API completa y el modelo de datos.
              </Paragraph>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
