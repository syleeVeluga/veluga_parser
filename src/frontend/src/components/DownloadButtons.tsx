import { getDownloadUrl, getChunksDownloadUrl } from '../services/api'

interface DownloadButtonsProps {
  jobId: string
  enabled: boolean
}

interface DownloadOption {
  label: string
  href: string
}

export function DownloadButtons({ jobId, enabled }: DownloadButtonsProps) {
  const options: DownloadOption[] = [
    { label: 'JSON', href: getDownloadUrl(jobId, 'json') },
    { label: 'Markdown', href: getDownloadUrl(jobId, 'markdown') },
    { label: 'Plain Text', href: getDownloadUrl(jobId, 'text') },
    { label: 'Chunks JSON', href: getChunksDownloadUrl(jobId) },
  ]

  return (
    <div className="flex gap-2 flex-wrap">
      {options.map(({ label, href }) => (
        <a
          key={label}
          href={enabled ? href : undefined}
          download
          aria-disabled={!enabled}
          className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium border transition-colors
            ${enabled
              ? 'border-blue-500 text-blue-600 hover:bg-blue-50 cursor-pointer'
              : 'border-gray-200 text-gray-400 cursor-not-allowed pointer-events-none'
            }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {label}
        </a>
      ))}
    </div>
  )
}
