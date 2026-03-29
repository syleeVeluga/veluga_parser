import { useState, useEffect, useCallback } from 'react'
import { Outlet, useNavigate, useParams } from 'react-router-dom'
import { Sidebar } from './Sidebar'

const SIDEBAR_KEY = 'veluga_sidebar_collapsed'

export function AppShell() {
  const navigate = useNavigate()
  const { jobId } = useParams<{ jobId: string }>()
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(SIDEBAR_KEY) === 'true'
    } catch {
      return false
    }
  })
  const [mobileOpen, setMobileOpen] = useState(false)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const toggleSidebar = useCallback(() => {
    setCollapsed(prev => {
      const next = !prev
      try {
        localStorage.setItem(SIDEBAR_KEY, String(next))
      } catch { /* ignore */ }
      return next
    })
  }, [])

  // Keyboard shortcut: Ctrl+B / Cmd+B
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault()
        // On mobile toggle overlay, on desktop toggle collapse
        if (window.innerWidth < 768) {
          setMobileOpen(prev => !prev)
        } else {
          toggleSidebar()
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [toggleSidebar])

  const handleSelectJob = useCallback(
    (id: string) => {
      navigate(`/jobs/${id}`)
      setMobileOpen(false)
    },
    [navigate],
  )

  const handleUploadComplete = useCallback(
    (id: string) => {
      setRefreshTrigger(prev => prev + 1)
      navigate(`/jobs/${id}`)
      setMobileOpen(false)
    },
    [navigate],
  )

  return (
    <div className="h-screen flex bg-gray-50 overflow-hidden">
      {/* Mobile overlay backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar — desktop: inline, mobile: overlay drawer */}
      <div
        className={`
          md:relative md:z-auto
          ${mobileOpen ? 'fixed inset-y-0 left-0 z-50' : 'hidden md:flex'}
        `}
      >
        <Sidebar
          collapsed={collapsed}
          onToggle={toggleSidebar}
          activeJobId={jobId ?? null}
          onSelectJob={handleSelectJob}
          onUploadComplete={handleUploadComplete}
          refreshTrigger={refreshTrigger}
        />
      </div>

      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed bottom-4 left-4 z-30 md:hidden bg-blue-600 text-white p-3 rounded-full shadow-lg"
        aria-label="Open sidebar"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        <Outlet />
      </div>
    </div>
  )
}
