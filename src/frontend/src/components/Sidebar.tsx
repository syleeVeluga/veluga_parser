import { useRef, useState, useEffect, type ChangeEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useUpload } from '../hooks/useUpload'
import { SidebarDocList } from './SidebarDocList'
import { EngineSelector } from './EngineSelector'
import { getApiKeyStatus, type EngineType } from '../services/api'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  activeJobId: string | null
  onSelectJob: (jobId: string) => void
  onUploadComplete: (jobId: string) => void
  refreshTrigger: number
}

export function Sidebar({
  collapsed,
  onToggle,
  activeJobId,
  onSelectJob,
  onUploadComplete,
  refreshTrigger,
}: SidebarProps) {
  const { state, error, upload } = useUpload()
  const inputRef = useRef<HTMLInputElement>(null)
  const location = useLocation()
  const [selectedEngine, setSelectedEngine] = useState<EngineType>('docling')
  const [geminiConfigured, setGeminiConfigured] = useState(false)

  useEffect(() => {
    getApiKeyStatus()
      .then(s => setGeminiConfigured(s.gemini_configured))
      .catch(() => {})
  }, [])

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      if (inputRef.current) inputRef.current.value = ''
      return
    }
    const result = await upload(file, selectedEngine)
    if (result) {
      onUploadComplete(result.job_id)
    }
    if (inputRef.current) inputRef.current.value = ''
  }

  const isUploading = state === 'uploading'

  if (collapsed) {
    return (
      <aside
        data-testid="sidebar"
        className="w-12 bg-white border-r border-gray-200 flex flex-col items-center py-3 gap-3 shrink-0"
      >
        <button
          onClick={onToggle}
          className="text-gray-500 hover:text-gray-700 p-1"
          title="Expand sidebar"
          aria-label="Expand sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <button
          onClick={() => !isUploading && inputRef.current?.click()}
          className="text-gray-500 hover:text-blue-600 p-1"
          title="Upload PDF"
          aria-label="Upload PDF"
          disabled={isUploading}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={handleFileChange}
          disabled={isUploading}
          aria-label="PDF file input"
        />
      </aside>
    )
  }

  return (
    <aside
      data-testid="sidebar"
      className="w-70 bg-white border-r border-gray-200 flex flex-col shrink-0 transition-all duration-200"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2 min-w-0">
          <svg className="w-5 h-5 text-blue-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <span className="text-sm font-bold text-gray-800 truncate">Veluga PDF Parser</span>
        </div>
        <button
          onClick={onToggle}
          className="text-gray-400 hover:text-gray-600 p-1 shrink-0"
          title="Collapse sidebar"
          aria-label="Collapse sidebar"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>

      {/* Engine selector */}
      <div className="px-3 py-2 border-b border-gray-100">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5 block">Engine</span>
        <EngineSelector
          value={selectedEngine}
          onChange={setSelectedEngine}
          geminiConfigured={geminiConfigured}
        />
      </div>

      {/* Upload button */}
      <div className="px-3 py-2 border-b border-gray-100">
        <button
          onClick={() => !isUploading && inputRef.current?.click()}
          disabled={isUploading}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {isUploading ? (
            <>
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Uploading...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Upload PDF
            </>
          )}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={handleFileChange}
          disabled={isUploading}
          aria-label="PDF file input"
        />
        {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
      </div>

      {/* Subheading */}
      <div className="px-3 pt-2 pb-1">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Documents</span>
      </div>

      {/* Document list */}
      <SidebarDocList
        activeJobId={activeJobId}
        onSelect={onSelectJob}
        refreshTrigger={refreshTrigger}
      />

      {/* Footer nav */}
      <div className="px-3 py-2 border-t border-gray-100 shrink-0">
        <Link
          to="/settings"
          data-testid="settings-nav-link"
          className={`flex items-center gap-2 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
            location.pathname === '/settings'
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
          }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Settings
        </Link>
      </div>
    </aside>
  )
}
