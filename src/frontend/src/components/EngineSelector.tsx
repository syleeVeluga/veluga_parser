import { Link } from 'react-router-dom'
import type { EngineType } from '../services/api'

interface Engine {
  id: EngineType
  label: string
  subtitle: string
}

const ENGINES: Engine[] = [
  { id: 'docling', label: 'Docling', subtitle: 'Local · Multi-lingual' },
  { id: 'paddleocr', label: 'PaddleOCR 3', subtitle: 'Local · CJK-optimised' },
  { id: 'gemini', label: 'Gemini Flash', subtitle: 'API · Vision-Language' },
]

interface EngineSelectorProps {
  value: EngineType
  onChange: (engine: EngineType) => void
  geminiConfigured: boolean
}

export function EngineSelector({ value, onChange, geminiConfigured }: EngineSelectorProps) {
  return (
    <div className="flex flex-col gap-1" role="radiogroup" aria-label="Extraction engine">
      {ENGINES.map(engine => {
        const isGemini = engine.id === 'gemini'
        const disabled = isGemini && !geminiConfigured
        const selected = value === engine.id

        return (
          <button
            key={engine.id}
            role="radio"
            aria-checked={selected}
            aria-disabled={disabled ? 'true' : undefined}
            data-engine={engine.id}
            disabled={disabled}
            onClick={() => !disabled && onChange(engine.id)}
            className={`
              flex items-center gap-2.5 w-full text-left px-2.5 py-1.5 rounded
              border transition-colors text-xs
              ${selected
                ? 'border-l-4 border-indigo-500 bg-indigo-50 border-r border-t border-b border-indigo-200'
                : 'border border-gray-200 hover:bg-gray-50'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            {/* Radio indicator */}
            <span className={`w-3 h-3 rounded-full border flex-shrink-0 flex items-center justify-center ${
              selected ? 'border-indigo-500 bg-indigo-500' : 'border-gray-300 bg-white'
            }`}>
              {selected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
            </span>

            <div className="flex-1 min-w-0">
              <span className={`font-medium ${selected ? 'text-indigo-800' : 'text-gray-700'}`}>
                {engine.label}
              </span>
              <span className="ml-1.5 text-gray-400">{engine.subtitle}</span>
            </div>

            {/* Gemini lock state */}
            {isGemini && !geminiConfigured && (
              <Link
                to="/settings"
                onClick={e => e.stopPropagation()}
                className="flex items-center gap-1 text-amber-600 hover:text-amber-700 text-xs shrink-0"
                data-testid="gemini-settings-link"
              >
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                <span>→ Settings</span>
              </Link>
            )}
          </button>
        )
      })}
    </div>
  )
}
