import { type TocEntry } from '../services/api'

interface TocSidebarProps {
  toc: TocEntry[]
  activePage: number
  onNavigate: (page: number) => void
}

export function TocSidebar({ toc, activePage, onNavigate }: TocSidebarProps) {
  if (toc.length === 0) {
    return (
      <div className="w-48 shrink-0">
        <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Contents</h3>
        <p className="text-xs text-gray-400 italic">No sections found</p>
      </div>
    )
  }

  return (
    <div className="w-48 shrink-0">
      <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Contents</h3>
      <ul className="space-y-0.5 max-h-[500px] overflow-y-auto">
        {toc.map(entry => {
          const indent = Math.max(0, entry.level) * 12
          const isActive = activePage === entry.page_number
          return (
            <li key={entry.element_id}>
              <button
                onClick={() => onNavigate(entry.page_number)}
                style={{ paddingLeft: `${indent + 8}px` }}
                className={`w-full text-left py-1 pr-2 rounded text-xs transition-colors leading-snug
                  ${isActive
                    ? 'text-blue-700 font-medium bg-blue-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                title={`p.${entry.page_number}`}
              >
                <span className="line-clamp-2">{entry.text}</span>
                <span className="text-gray-400 font-normal block text-[10px]">p.{entry.page_number}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
