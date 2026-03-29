import { useState } from 'react'
import { uploadPdf, type EngineType, type UploadResponse } from '../services/api'

type UploadState = 'idle' | 'uploading' | 'error'

interface UseUploadResult {
  state: UploadState
  error: string | null
  upload: (file: File, engine?: EngineType) => Promise<UploadResponse | null>
  reset: () => void
}

export function useUpload(): UseUploadResult {
  const [state, setState] = useState<UploadState>('idle')
  const [error, setError] = useState<string | null>(null)

  const upload = async (file: File, engine?: EngineType): Promise<UploadResponse | null> => {
    setState('uploading')
    setError(null)
    try {
      const result = await uploadPdf(file, engine)
      setState('idle')
      return result
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      setState('error')
      setError(message)
      return null
    }
  }

  const reset = () => {
    setState('idle')
    setError(null)
  }

  return { state, error, upload, reset }
}
