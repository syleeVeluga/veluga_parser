import { useState, useEffect } from 'react'
import { getApiKeyStatus, saveGeminiApiKey } from '../services/api'

export function SettingsPage() {
  const [geminiKey, setGeminiKey] = useState('')
  const [configured, setConfigured] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savedBadge, setSavedBadge] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getApiKeyStatus()
      .then(s => setConfigured(s.gemini_configured))
      .catch(() => {})
  }, [])

  const handleSave = async () => {
    if (!geminiKey.trim()) return
    setSaving(true)
    setError(null)
    try {
      const result = await saveGeminiApiKey(geminiKey.trim())
      setConfigured(result.gemini_configured)
      setGeminiKey('')
      setSavedBadge(true)
      setTimeout(() => setSavedBadge(false), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save API key')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex-1 overflow-auto bg-gray-50">
      <div className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-6">Settings</h1>

        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-sm font-semibold text-gray-800">Gemini API Key</h2>
            {configured && (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-2 py-0.5">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586l-3.293-3.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" clipRule="evenodd" />
                </svg>
                Configured
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mb-3">
            Required to use the Gemini Flash extraction engine.
            The key is stored server-side and never returned by the API.
          </p>

          <label htmlFor="gemini-api-key" className="block text-xs font-medium text-gray-700 mb-1">
            Gemini API Key
          </label>
          <div className="flex gap-2">
            <input
              id="gemini-api-key"
              type="password"
              value={geminiKey}
              onChange={e => setGeminiKey(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSave()}
              placeholder={configured ? '••••••••  (key already set — enter to replace)' : 'Enter your Gemini API key'}
              className="flex-1 text-sm px-3 py-1.5 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <button
              onClick={handleSave}
              disabled={saving || !geminiKey.trim()}
              className="shrink-0 px-3 py-1.5 text-sm font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {savedBadge ? (
                <span className="flex items-center gap-1 text-emerald-300">
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586l-3.293-3.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" clipRule="evenodd" />
                  </svg>
                  Saved
                </span>
              ) : saving ? 'Saving…' : 'Save'}
            </button>
          </div>

          {error && (
            <p className="mt-2 text-xs text-red-600" role="alert">{error}</p>
          )}
        </div>
      </div>
    </div>
  )
}
