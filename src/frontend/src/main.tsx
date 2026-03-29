import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './styles/index.css'
import { AppShell } from './components/AppShell'
import { MainContent } from './components/MainContent'
import { SettingsPage } from './pages/SettingsPage'

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <MainContent /> },
      { path: 'jobs/:jobId', element: <MainContent /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
])

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('Root element not found')

createRoot(rootElement).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
