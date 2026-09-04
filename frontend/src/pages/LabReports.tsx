import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageWrapper, Card, Badge, Button, Spinner } from '../components/ui'
import { listReports, uploadReport, type ReportSummary } from '../services/labService'
import { Upload, FlaskConical, AlertTriangle, CheckCircle2, X } from 'lucide-react'

interface UploadState {
  file: File | null
  labName: string
  reportDate: string
  uploading: boolean
  error: string | null
  success: string | null
}

export function LabReports() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [reports, setReports] = useState<ReportSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)
  const [upload, setUpload] = useState<UploadState>({
    file: null, labName: '', reportDate: '',
    uploading: false, error: null, success: null,
  })

  const fetchReports = () => {
    setLoading(true)
    listReports()
      .then(setReports)
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchReports() }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null
    setUpload(u => ({ ...u, file: f, error: null, success: null }))
  }

  const handleUpload = async () => {
    if (!upload.file) return
    setUpload(u => ({ ...u, uploading: true, error: null, success: null }))
    try {
      const result = await uploadReport(
        upload.file,
        upload.labName || 'Unknown Lab',
        upload.reportDate || new Date().toISOString().slice(0, 10),
      )
      setUpload(u => ({
        ...u, uploading: false,
        success: `${result.biomarkers.length} biomarkers extracted successfully.`,
        file: null, labName: '', reportDate: '',
      }))
      fetchReports()
      setTimeout(() => setShowUpload(false), 2000)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? 'Upload failed. Please try again.'
      setUpload(u => ({ ...u, uploading: false, error: msg }))
    }
  }

  return (
    <PageWrapper
      title="Lab Reports"
      subtitle="Upload and analyze your laboratory reports"
      action={
        <Button size="sm" onClick={() => setShowUpload(v => !v)}>
          <Upload size={14} /> Upload Report
        </Button>
      }
    >
      <div className="space-y-4">

        {/* Upload panel */}
        {showUpload && (
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[#F9FAFB] font-semibold text-sm">Upload Lab Report PDF</h3>
              <button onClick={() => setShowUpload(false)} className="text-[#6B7280] hover:text-[#F9FAFB]">
                <X size={16} />
              </button>
            </div>

            <div className="space-y-3">
              {/* File drop zone */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className={[
                  'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors',
                  upload.file
                    ? 'border-[#10B981] bg-[#10B981]/5'
                    : 'border-[#1F2937] hover:border-[#374151]',
                ].join(' ')}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={handleFileChange}
                />
                {upload.file ? (
                  <div className="flex items-center justify-center gap-2">
                    <CheckCircle2 size={16} className="text-[#10B981]" />
                    <span className="text-[#10B981] text-sm font-medium">{upload.file.name}</span>
                  </div>
                ) : (
                  <>
                    <Upload size={20} className="text-[#6B7280] mx-auto mb-2" />
                    <p className="text-[#9CA3AF] text-sm">Click to choose a PDF</p>
                    <p className="text-[#6B7280] text-xs mt-1">
                      Chughtai Lab, Dr. Essa Lab, and standard Pakistani lab formats supported
                    </p>
                  </>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Lab Name (optional)</label>
                  <input
                    type="text"
                    value={upload.labName}
                    onChange={e => setUpload(u => ({ ...u, labName: e.target.value }))}
                    placeholder="e.g. Chughtai Lab"
                    className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none focus:border-[#0EA5E9] transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Report Date (optional)</label>
                  <input
                    type="date"
                    value={upload.reportDate}
                    onChange={e => setUpload(u => ({ ...u, reportDate: e.target.value }))}
                    className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] outline-none focus:border-[#0EA5E9] transition-colors"
                  />
                </div>
              </div>

              {upload.error && (
                <div className="flex items-start gap-2 bg-[#EF4444]/10 border border-[#EF4444]/20 rounded-lg p-3">
                  <AlertTriangle size={14} className="text-[#EF4444] shrink-0 mt-0.5" />
                  <p className="text-[#EF4444] text-xs">{upload.error}</p>
                </div>
              )}

              {upload.success && (
                <div className="flex items-center gap-2 bg-[#10B981]/10 border border-[#10B981]/20 rounded-lg p-3">
                  <CheckCircle2 size={14} className="text-[#10B981]" />
                  <p className="text-[#10B981] text-xs">{upload.success}</p>
                </div>
              )}

              <Button
                onClick={handleUpload}
                disabled={!upload.file}
                loading={upload.uploading}
                className="w-full"
              >
                {upload.uploading ? 'Extracting biomarkers…' : 'Upload & Extract'}
              </Button>

              <p className="text-[#6B7280] text-xs text-center">
                HealthOS extracts biomarker values from your PDF using deterministic parsing. No data is sent to external servers during extraction.
              </p>
            </div>
          </Card>
        )}

        {/* Reports list */}
        {loading ? (
          <div className="flex justify-center py-12"><Spinner label="Loading reports…" /></div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12">
            <FlaskConical size={32} className="text-[#374151] mx-auto mb-3" />
            <p className="text-[#9CA3AF] text-sm">No lab reports uploaded yet</p>
            <p className="text-[#6B7280] text-xs mt-1">Click Upload Report to add your first report</p>
          </div>
        ) : (
          reports.map(r => (
            <Card
              key={r.id}
              onClick={() => navigate(`/lab-reports/${r.id}`)}
              className="cursor-pointer hover:border-[#374151] transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-[#0EA5E9]/10 border border-[#0EA5E9]/20 flex items-center justify-center shrink-0">
                    <FlaskConical size={16} className="text-[#0EA5E9]" />
                  </div>
                  <div>
                    <h3 className="text-[#F9FAFB] font-medium text-sm">{r.filename}</h3>
                    <p className="text-[#9CA3AF] text-xs mt-0.5">{r.lab_name}</p>
                    <p className="text-[#6B7280] text-xs">Report date: {r.report_date}</p>
                  </div>
                </div>
                <div className="text-right shrink-0 ml-3">
                  <p className="text-[#F9FAFB] text-sm font-semibold">{r.total_biomarkers} biomarkers</p>
                  {r.abnormal_count > 0
                    ? <Badge label={`${r.abnormal_count} outside range`} variant="high" />
                    : <Badge label="All normal" variant="normal" />
                  }
                </div>
              </div>
            </Card>
          ))
        )}

        {/* Manual entry link */}
        <p className="text-center text-xs text-[#6B7280]">
          PDF not parsing correctly?{' '}
          <button className="text-[#0EA5E9] hover:underline">Use manual entry instead</button>
        </p>
      </div>
    </PageWrapper>
  )
}
