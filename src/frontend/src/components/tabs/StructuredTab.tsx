import { ResultsViewer } from '../ResultsViewer'

interface StructuredTabProps {
  jobId: string
  filename: string
}

export function StructuredTab({ jobId, filename }: StructuredTabProps) {
  return (
    <div className="p-2">
      <ResultsViewer jobId={jobId} filename={filename} status="completed" />
    </div>
  )
}
