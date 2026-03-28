import { useState, useEffect, useRef } from 'react'
import { getJob, type JobSummary } from '../services/api'

interface UseJobStatusResult {
  job: JobSummary | null
  loading: boolean
  error: string | null
}

const TERMINAL_STATUSES = new Set(['completed', 'failed'])
const POLL_INTERVAL_MS = 2000

export function useJobStatus(jobId: string): UseJobStatusResult {
  const [job, setJob] = useState<JobSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const errorCountRef = useRef(0)

  useEffect(() => {
    let cancelled = false

    const fetchJob = async () => {
      try {
        const data = await getJob(jobId)
        if (!cancelled) {
          errorCountRef.current = 0
          setJob(data)
          setError(null)
          if (TERMINAL_STATUSES.has(data.status)) {
            if (intervalRef.current) {
              clearInterval(intervalRef.current)
              intervalRef.current = null
            }
          }
        }
      } catch (err) {
        if (!cancelled) {
          errorCountRef.current += 1
          setError(err instanceof Error ? err.message : 'Failed to fetch job')
          if (errorCountRef.current >= 3 && intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
          }
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchJob()
    intervalRef.current = setInterval(fetchJob, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [jobId])

  return { job, loading, error }
}
