import { useState, useRef, type ChangeEvent } from 'react'
import { useUpload } from '../hooks/useUpload'
import { useNavigate } from 'react-router-dom'

export function UploadZone() {
  const { state, error, upload } = useUpload()
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [validationError, setValidationError] = useState<string | null>(null)

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setValidationError('Please select a PDF file.')
      if (inputRef.current) inputRef.current.value = ''
      return
    }
    setValidationError(null)

    const result = await upload(file)
    if (result) {
      navigate(`/jobs/${result.job_id}`)
    }
    if (inputRef.current) inputRef.current.value = ''
  }

  const isUploading = state === 'uploading'

  return (
    <div className="w-full">
      <div
        className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center hover:border-blue-400 transition-colors cursor-pointer bg-gray-50"
        onClick={() => !isUploading && inputRef.current?.click()}
        role="button"
        aria-label="Upload PDF"
      >
        <div className="flex flex-col items-center gap-3">
          <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {isUploading ? (
            <p className="text-blue-600 font-medium">Uploading...</p>
          ) : (
            <>
              <p className="text-gray-700 font-medium">Click to select a PDF file</p>
              <p className="text-sm text-gray-500">
                Supports: Korean, English, Japanese, Chinese
              </p>
            </>
          )}
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        onChange={handleFileChange}
        disabled={isUploading}
        aria-label="PDF file input"
      />
      {(validationError || error) && (
        <p className="mt-2 text-sm text-red-600" role="alert">{validationError ?? error}</p>
      )}
    </div>
  )
}
