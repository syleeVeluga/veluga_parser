import { UploadZone } from '../components/UploadZone'
import { JobList } from '../components/JobList'

export function HomePage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">Upload PDF</h2>
        <UploadZone />
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-4">Recent Jobs</h2>
        <JobList />
      </div>
    </div>
  )
}
