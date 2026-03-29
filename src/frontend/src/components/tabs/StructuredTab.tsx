import { useState, useEffect } from 'react'
import { getToc, type TocEntry } from '../../services/api'
import { ResultsViewer } from '../ResultsViewer'
import { TocSidebar } from '../TocSidebar'

interface StructuredTabProps {
  jobId: string
  filename: string
}

export function StructuredTab({ jobId, filename }: StructuredTabProps) {
  const [toc, setToc] = useState<TocEntry[]>([])
  const [activePage, setActivePage] = useState(1)

  useEffect(() => {
    getToc(jobId)
      .then(data => setToc(data.toc))
      .catch(() => setToc([]))
  }, [jobId])

  return (
    <div className="p-2">
      <div className="flex gap-4">
        {/* TOC sidebar */}
        <TocSidebar
          toc={toc}
          activePage={activePage}
          onNavigate={setActivePage}
        />

        {/* Results viewer */}
        <div className="flex-1 min-w-0">
          <ResultsViewer
            jobId={jobId}
            filename={filename}
            status="completed"
            activePage={activePage}
            onPageChange={setActivePage}
          />
        </div>
      </div>
    </div>
  )
}
