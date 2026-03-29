import Split from 'react-split'
import { PdfPane } from './PdfPane'
import { OutputPane } from './OutputPane'

interface SplitPaneViewerProps {
  jobId: string
  filename: string
}

export function SplitPaneViewer({ jobId, filename }: SplitPaneViewerProps) {
  return (
    <div className="w-full h-full overflow-hidden">
      <Split
        className="flex h-full"
        sizes={[50, 50]}
        minSize={300}
        gutterSize={8}
        gutterStyle={() => ({
          backgroundColor: '#e5e7eb',
          cursor: 'col-resize',
          flexShrink: '0',
        })}
      >
        {/* Left: original PDF */}
        <div className="h-full overflow-hidden">
          <PdfPane jobId={jobId} />
        </div>

        {/* Right: parsed output tabs */}
        <div className="h-full overflow-hidden">
          <OutputPane jobId={jobId} filename={filename} />
        </div>
      </Split>
    </div>
  )
}
