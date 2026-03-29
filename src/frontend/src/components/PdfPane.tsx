import { useState, useCallback, useEffect, useRef } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import { getPdfUrl } from '../services/api'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

interface PdfPaneProps {
  jobId: string
}

export function PdfPane({ jobId }: PdfPaneProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [containerWidth, setContainerWidth] = useState<number>(600)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver(entries => {
      setContainerWidth(entries[0].contentRect.width)
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setPageNumber(1)
  }, [])

  const goToPrev = () => setPageNumber(p => Math.max(1, p - 1))
  const goToNext = () => setPageNumber(p => Math.min(numPages, p + 1))

  return (
    <div className="h-full flex flex-col bg-gray-100 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-white border-b text-sm shrink-0">
        <span className="text-gray-600 font-medium">Original PDF</span>
        {numPages > 0 && (
          <div className="flex items-center gap-1">
            <button
              onClick={goToPrev}
              disabled={pageNumber <= 1}
              className="px-2 py-1 rounded text-gray-600 disabled:opacity-30 hover:bg-gray-100 text-base leading-none"
            >
              ‹
            </button>
            <span className="text-gray-700 px-1 min-w-[5rem] text-center">
              {pageNumber} / {numPages}
            </span>
            <button
              onClick={goToNext}
              disabled={pageNumber >= numPages}
              className="px-2 py-1 rounded text-gray-600 disabled:opacity-30 hover:bg-gray-100 text-base leading-none"
            >
              ›
            </button>
          </div>
        )}
      </div>
      <div ref={containerRef} className="flex-1 overflow-auto flex justify-center py-4 px-2">
        <Document
          file={getPdfUrl(jobId)}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div className="text-gray-400 text-sm mt-16">Loading PDF…</div>
          }
          error={
            <div className="text-red-500 text-sm mt-16 px-4 text-center">
              Failed to load PDF. The file may still be processing.
            </div>
          }
        >
          <Page
            pageNumber={pageNumber}
            width={Math.max(containerWidth - 16, 200)}
            renderTextLayer
            renderAnnotationLayer
            className="shadow-lg"
          />
        </Document>
      </div>
    </div>
  )
}
