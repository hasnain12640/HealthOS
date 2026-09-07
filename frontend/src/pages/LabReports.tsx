import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageWrapper, Card, Badge, Button, Spinner } from '../components/ui'
import { listReports, uploadReport, type ReportSummary } from '../services/labService'
import { ManualEntryModal } from '../components/lab/ManualEntryModal'
import { Upload, FlaskConical, AlertTriangle, CheckCircle2, X } from 'lucide-react'

interface UploadState {
  file: File | null
  labName: string
  reportDate: string
  uploading: boolean
  error: string | null
  warning: string | null
  success: string | null
}

export function LabReports() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [reports, setReports] = useState<ReportSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)
  const [showManual, setShowManual] = useState(false)
  const [upload, setUpload] = useState<UploadState>({
    file: null, labName: '', reportDate: '',
    uploading: false, error: null, warning: null, success: null,
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
    setUpload(u => ({ ...u, file: f, error: null, warning: null, success: null }))
  }

  const handleUpload = async () => {
    if (!upload.file) return
    setUpload(u => ({ ...u, uploading: true, error: null, warning: null, success: null }))
    try {
      const result = await uploadReport(
        upload.file,
        upload.labName || 'Unknown Lab',
        upload.reportDate || new Date().toISOString().slice(0, 10),
      )
      setUpload(u => ({
        ...u,
        uploading: false,
        warning: result.warning,
        success: result.warning ? null : `${result.biomarkers.length} biomarkers extracted successfully.`,
        file: null,
        labName: '',
        reportDate: '',
      }))
      fetchReports()
      if (!result.warning) setTimeout(() => setShowUpload(false), 2000)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? 'Upload failed. Please try again.'
      setUpload(u => ({ ...u, uploading: false, error: msg, warning: null }))
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
              <h3 className="text-text-primary font-semibold text-sm">Upload Lab Report PDF</h3>
              <button onClick={() => setShowUpload(false)} className="text-text-muted hover:text-text-primary">
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
                    ? 'border-accent bg-accent/5'
                    : 'border-border-subtle hover:border-border',
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
                    <CheckCircle2 size={16} className="text-accent" />
                    <span className="text-accent text-sm font-medium">{upload.file.name}</span>
                  </div>
                ) : (
                  <>
                    <Upload size={20} className="text-text-muted mx-auto mb-2" />
                    <p className="text-text-secondary text-sm">Click to choose a PDF</p>
                    <p className="text-text-muted text-xs mt-1">
                      Chughtai Lab, Dr. Essa Lab, and standard Pakistani lab formats supported
                    </p>
                  </>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-text-secondary text-xs mb-1">Lab Name (optional)</label>
                  <input
                    type="text"
                    value={upload.labName}
                    onChange={e => setUpload(u => ({ ...u, labName: e.target.value }))}
                    placeholder="e.g. Chughtai Lab"
                    className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-text-secondary text-xs mb-1">Report Date (optional)</label>
                  <input
                    type="date"
                    value={upload.reportDate}
                    onChange={e => setUpload(u => ({ ...u, reportDate: e.target.value }))}
                    className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-primary transition-colors"
                  />
                </div>
              </div>

              {upload.error && (
                <div className="flex items-start gap-2 bg-danger/10 border border-danger/20 rounded-lg p-3">
                  <AlertTriangle size={14} className="text-danger shrink-0 mt-0.5" />
                  <p className="text-danger text-xs">{upload.error}</p>
                </div>
              )}

              {upload.warning && (
                <div className="flex items-start gap-2 bg-primary/10 border border-primary/20 rounded-lg p-3">
                  <AlertTriangle size={14} className="text-primary shrink-0 mt-0.5" />
                  <p className="text-primary text-xs">{upload.warning}</p>
                </div>
              )}

              {upload.success && (
                <div className="flex items-center gap-2 bg-accent/10 border border-accent/20 rounded-lg p-3">
                  <CheckCircle2 size={14} className="text-accent" />
                  <p className="text-accent text-xs">{upload.success}</p>
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

              <p className="text-text-muted text-xs text-center">
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
            <FlaskConical size={32} className="text-border-subtle mx-auto mb-3" />
            <p className="text-text-secondary text-sm">No lab reports uploaded yet</p>
            <p className="text-text-muted text-xs mt-1">Click Upload Report to add your first report</p>
          </div>
        ) : (
          reports.map(r => (
            <Card
              key={r.id}
              onClick={() => navigate(`/lab-reports/${r.id}`)}
              className="cursor-pointer hover:border-border-subtle transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                    <FlaskConical size={16} className="text-primary" />
                  </div>
                  <div>
                    <h3 className="text-text-primary font-medium text-sm">{r.filename}</h3>
                    <p className="text-text-secondary text-xs mt-0.5">{r.lab_name}</p>
                    <p className="text-text-muted text-xs">Report date: {r.report_date}</p>
                  </div>
                </div>
                <div className="text-right shrink-0 ml-3">
                  <p className="text-text-primary text-sm font-semibold">{r.total_biomarkers} biomarkers</p>
                  {r.total_biomarkers === 0
                    ? <Badge label="No biomarkers extracted" variant="default" />
                    : r.abnormal_count > 0
                      ? <Badge label={`${r.abnormal_count} outside range`} variant="high" />
                      : <Badge label="All normal" variant="normal" />
                  }
                </div>
              </div>
            </Card>
          ))
        )}

        {/* Manual entry link */}
        <p className="text-center text-xs text-text-muted">
          PDF not parsing correctly?{' '}
          <button
            type="button"
            onClick={() => setShowManual(true)}
            className="text-primary hover:underline"
          >
            Use manual entry instead
          </button>
        </p>
      </div>

      <ManualEntryModal
        open={showManual}
        onClose={() => setShowManual(false)}
        onSuccess={() => { fetchReports(); setShowManual(false); }}
      />
    </PageWrapper>
  )
}
