import { useState } from 'react'
import { MarkdownTab } from './tabs/MarkdownTab'
import { JsonTab } from './tabs/JsonTab'
import { PlainTextTab } from './tabs/PlainTextTab'
import { StructuredTab } from './tabs/StructuredTab'
import { ChunksTab } from './tabs/ChunksTab'

type Tab = 'markdown' | 'json' | 'text' | 'structure' | 'chunks'

const TABS: { id: Tab; label: string }[] = [
  { id: 'markdown', label: 'Markdown' },
  { id: 'json', label: 'JSON' },
  { id: 'text', label: 'Text' },
  { id: 'structure', label: 'Structure' },
  { id: 'chunks', label: 'Chunks' },
]

interface OutputPaneProps {
  jobId: string
  filename: string
}

export function OutputPane({ jobId, filename }: OutputPaneProps) {
  const [activeTab, setActiveTab] = useState<Tab>('markdown')

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Tab bar */}
      <div className="flex border-b border-gray-200 shrink-0">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px
              ${activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'markdown' && <MarkdownTab jobId={jobId} />}
        {activeTab === 'json' && <JsonTab jobId={jobId} />}
        {activeTab === 'text' && <PlainTextTab jobId={jobId} />}
        {activeTab === 'structure' && <StructuredTab jobId={jobId} filename={filename} />}
        {activeTab === 'chunks' && <ChunksTab jobId={jobId} />}
      </div>
    </div>
  )
}
