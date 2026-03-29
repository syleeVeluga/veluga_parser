import { useState, useEffect } from 'react'
import { getStructure, type StructureProfile } from '../../services/api'

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color =
    pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-400'
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-medium text-gray-700 w-12 text-right">
        {pct}%
      </span>
    </div>
  )
}

function FontSizeHistogram({
  histogram,
  bodySize,
  headingSizes,
}: {
  histogram: Record<string, number>
  bodySize: number | null
  headingSizes: Set<number>
}) {
  const entries = Object.entries(histogram)
    .map(([size, count]) => ({ size: parseFloat(size), count }))
    .sort((a, b) => a.size - b.size)

  if (entries.length === 0) {
    return <p className="text-sm text-gray-400 italic">No font data available</p>
  }

  const maxCount = Math.max(...entries.map(e => e.count))

  return (
    <div className="space-y-1.5">
      {entries.map(({ size, count }) => {
        const isBody = bodySize !== null && size === bodySize
        const isHeading = headingSizes.has(size)
        const barColor = isBody
          ? 'bg-blue-500'
          : isHeading
            ? 'bg-amber-500'
            : 'bg-gray-300'
        const label = isBody ? 'Body' : isHeading ? 'Heading' : ''
        return (
          <div key={size} className="flex items-center gap-2 text-xs">
            <span className="w-12 text-right font-mono text-gray-600 shrink-0">
              {size}pt
            </span>
            <div className="flex-1 h-5 bg-gray-100 rounded overflow-hidden relative">
              <div
                className={`h-full ${barColor} rounded transition-all`}
                style={{ width: `${Math.max(2, (count / maxCount) * 100)}%` }}
              />
              <span className="absolute inset-0 flex items-center px-2 text-gray-700 font-medium">
                {count.toLocaleString()}
              </span>
            </div>
            {label && (
              <span
                className={`text-xs px-1.5 py-0.5 rounded shrink-0 ${
                  isBody
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-amber-100 text-amber-700'
                }`}
              >
                {label}
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}

function TypographyHierarchy({ profile }: { profile: StructureProfile }) {
  const items: Array<{ label: string; name: string; size: number; level: string }> = []

  if (profile.heading_fonts.length > 0) {
    for (const h of profile.heading_fonts) {
      items.push({
        label: `H${h.level}`,
        name: h.name,
        size: h.size,
        level: `Heading ${h.level}`,
      })
    }
  }

  if (profile.body_font) {
    items.push({
      label: 'Body',
      name: profile.body_font.name,
      size: profile.body_font.size,
      level: 'Body Text',
    })
  }

  if (profile.page_number_font) {
    items.push({
      label: 'Pg#',
      name: profile.page_number_font.name,
      size: profile.page_number_font.size,
      level: 'Page Number',
    })
  }

  if (items.length === 0) {
    return <p className="text-sm text-gray-400 italic">No typography data</p>
  }

  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <div
          key={i}
          className="flex items-center gap-3 p-2 rounded border border-gray-100 bg-gray-50"
        >
          <span className="w-12 text-center text-xs font-bold text-white bg-gray-600 rounded py-1 shrink-0">
            {item.label}
          </span>
          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium text-gray-800">
              {item.level}
            </span>
            <span className="text-xs text-gray-500 ml-2">
              {item.name} / {item.size}pt
            </span>
          </div>
          <span
            className="font-serif text-gray-700 shrink-0"
            style={{ fontSize: `${Math.min(item.size * 1.2, 28)}px` }}
          >
            Aa
          </span>
        </div>
      ))}
    </div>
  )
}

function ReclassifiedList({
  items,
}: {
  items: StructureProfile['reclassified_elements']
}) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-gray-400 italic">
        No reclassification suggestions -- Docling labels match font analysis.
      </p>
    )
  }

  return (
    <div className="space-y-1.5 max-h-60 overflow-y-auto">
      {items.map((item, i) => (
        <div
          key={i}
          className="flex items-center gap-2 p-2 rounded border border-amber-100 bg-amber-50 text-xs"
        >
          <span className="font-mono text-gray-500 shrink-0">
            {item.element_id}
          </span>
          <span className="px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded">
            {item.original_type}
          </span>
          <span className="text-gray-400">&rarr;</span>
          <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
            {item.suggested_type}
          </span>
          <span className="text-gray-500 truncate" title={item.reason}>
            {item.font_size}pt
          </span>
        </div>
      ))}
    </div>
  )
}

interface StructureAnalysisTabProps {
  jobId: string
}

export function StructureAnalysisTab({ jobId }: StructureAnalysisTabProps) {
  const [profile, setProfile] = useState<StructureProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    getStructure(jobId)
      .then(data => {
        setProfile(data.structure_profile)
        setError(null)
      })
      .catch(err => {
        setError(err instanceof Error ? err.message : 'Failed to load structure')
      })
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) {
    return <p className="p-4 text-sm text-gray-500">Loading structure analysis...</p>
  }
  if (error) {
    return <p className="p-4 text-sm text-red-600">{error}</p>
  }
  if (!profile || !profile.body_font) {
    return (
      <div className="p-4 text-sm text-gray-500">
        <p className="font-medium">No structure analysis available.</p>
        <p className="mt-1 text-xs text-gray-400">
          This may be a scanned PDF without embedded text objects.
        </p>
      </div>
    )
  }

  const headingSizes = new Set(profile.heading_fonts.map(h => h.size))

  return (
    <div className="p-4 space-y-6 max-w-2xl">
      {/* Confidence */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">
          Structure Confidence
        </h3>
        <ConfidenceBar value={profile.structure_confidence} />
      </section>

      {/* Typography Hierarchy */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">
          Typography Hierarchy
        </h3>
        <TypographyHierarchy profile={profile} />
      </section>

      {/* Font Size Histogram */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">
          Font Size Distribution
        </h3>
        <FontSizeHistogram
          histogram={profile.font_size_histogram}
          bodySize={profile.body_font?.size ?? null}
          headingSizes={headingSizes}
        />
      </section>

      {/* Reclassifications */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">
          Reclassification Suggestions
          {profile.reclassified_elements.length > 0 && (
            <span className="ml-2 px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded text-xs font-normal">
              {profile.reclassified_elements.length}
            </span>
          )}
        </h3>
        <ReclassifiedList items={profile.reclassified_elements} />
      </section>

      {/* Running Header / Page Number */}
      {(profile.running_header_font || profile.page_number_font) && (
        <section>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            Repeating Elements
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            {profile.running_header_font && (
              <div className="p-2 bg-gray-50 rounded border border-gray-100">
                <div className="font-medium text-gray-600">Running Header</div>
                <div className="text-gray-500">
                  {profile.running_header_font.name} /{' '}
                  {profile.running_header_font.size}pt
                </div>
              </div>
            )}
            {profile.page_number_font && (
              <div className="p-2 bg-gray-50 rounded border border-gray-100">
                <div className="font-medium text-gray-600">Page Number</div>
                <div className="text-gray-500">
                  {profile.page_number_font.name} /{' '}
                  {profile.page_number_font.size}pt
                </div>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  )
}
