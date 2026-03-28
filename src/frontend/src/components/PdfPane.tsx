import { getPdfUrl } from '../services/api'

interface PdfPaneProps {
  jobId: string
}

export function PdfPane({ jobId }: PdfPaneProps) {
  return (
    <div className="h-full overflow-hidden bg-gray-100 flex flex-col">
      <iframe
        src={getPdfUrl(jobId)}
        className="w-full flex-1 border-0"
        title="Original PDF"
      >
        <p className="p-4 text-sm text-gray-500">
          Your browser does not support inline PDF viewing.
          Use the download button above to view the file.
        </p>
      </iframe>
    </div>
  )
}
