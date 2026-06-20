import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ConfigProvider, theme } from 'antd'
import esES from 'antd/locale/es_ES'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <ConfigProvider
        locale={esES}
        theme={{
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: '#1A6B6B',
            colorSuccess: '#6B8F3A',
            colorWarning: '#D4943A',
            colorError: '#C44A4A',
            colorInfo: '#1A6B6B',
            borderRadius: 8,
            fontFamily: "'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            colorBgLayout: '#F8F4EF',
            colorBgContainer: '#FFFFFF',
            colorBorder: '#E8E2DA',
            colorText: '#2D2A24',
            colorTextSecondary: '#7A736C',
            colorTextTertiary: '#A39B93',
          },
          components: {
            Menu: {
              colorItemBg: 'transparent',
              colorItemText: 'rgba(255,255,255,0.65)',
              colorItemTextHover: '#fff',
              colorItemTextSelected: '#fff',
              colorItemBgSelected: 'rgba(255,255,255,0.10)',
              colorItemBgHover: 'rgba(255,255,255,0.06)',
              colorGroupTitle: 'rgba(255,255,255,0.45)',
              colorSubItemBg: 'transparent',
              fontFamily: "'DM Sans', sans-serif",
              itemBorderRadius: 8,
              itemMarginInline: 8,
            },
            Layout: {
              colorBgHeader: '#FFFFFF',
              colorBgBody: '#F8F4EF',
            },
            Table: {
              colorBgContainer: '#FFFFFF',
              headerBg: '#F8F4EF',
              headerColor: '#7A736C',
              rowHoverBg: '#F0F7F7',
              borderColor: '#E8E2DA',
              fontFamily: "'DM Sans', sans-serif",
            },
            Card: {
              colorBgContainer: '#FFFFFF',
              paddingLG: 20,
            },
            Modal: {
              contentBg: '#FFFFFF',
              headerBg: '#FFFFFF',
            },
            Statistic: {
              fontFamily: "'DM Sans', sans-serif",
            },
          },
        }}
      >
        <App />
      </ConfigProvider>
    </ErrorBoundary>
  </StrictMode>,
)

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  })
}
