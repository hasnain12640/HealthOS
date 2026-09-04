import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { PageWrapper, Card, Spinner } from '../components/ui'
import { getReportDetail, type ReportDetail, type BiomarkerData } from '../services/labService'
import { ChevronLeft, AlertTriangle } from 'lucide-react'

function statusColor(status: string): string {
  return { normal: '#10B981', low: '#F59E0B', high: '#EF4444', critical: '#DC2626' }[status] ?? '#6B7280'
}

function statusBg(status: string): string {
  return { normal: 'bg-[#10B981]/10 border-[#10B981]/20 text-[#10B981]',
           low:    'bg-[#F59E0B]/10 border-[#F59E0B]/20 text-[#F59E0B]',
           high:   'bg-[#EF4444]/10 border-[#EF4444]/20 text-[#EF4444]',
           critical:'bg-[#DC2626]/10 border-[#DC2626]/20 text-[#DC2626]' }[status]
    ?? 'bg-[#1F2937] border-[#374151] text-[#9CA3AF]'
}

function BiomarkerRow({ b }: { b: BiomarkerData }) {
  const hasRange = b.reference_low !== null || b.reference_high !== null
  const refStr = !hasRange ? 'No reference'
    : b.reference_low !== null && b.reference_high !== null
      ? `${b.reference_low} – ${b.reference_high} ${b.unit}`
      : b.reference_high !== null ? `< ${b.reference_high} ${b.unit}`
      : `> ${b.reference_low} ${b.unit}`

  // Bar: show value as % of reference_high (or reference_low if only low)
  let barPct = 50
  const ref = b.reference_high ?? b.reference_low
  if (ref && ref > 0) barPct = Math.min(Math.round((b.value / ref) * 100), 120)
  const barWidth = Math.min(barPct, 100)

  return (
    <div className="bg-[#1F2937] rounded-xl p-3.5">
      <div className="flex items-start justify-between mb-2.5">
        <div>
          <p className="text-[#F9FAFB] text-sm font-medium">{b.name}</p>
          <p className="text-[#6B7280] text-xs capitalize">{b.category}</p>
        </div>
        <div className="text-right">
          <p className="text-[#F9FAFB] font-bold">
            {b.value.toLocaleString()}
            <span className="text-[#6B7280] font-normal text-xs ml-1">{b.unit}</span>
          </p>
          <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border font-medium ${statusBg(b.status)}`}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColor(b.status) }} />
            {b.status.charAt(0).toUpperCase() + b.status.slice(1)}
          </span>
        </div>
      </div>

      {/* Reference bar */}
      <div className="h-1.5 bg-[#374151] rounded-full overflow-hidden mb-1.5">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${barWidth}%`, backgroundColor: statusColor(b.status) }}
        />
      </div>
      <p className="text-[#6B7280] text-[11px]">Reference range: {refStr}</p>
    </div>
  )
}

export function LabReportDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [report, setReport] = useState<ReportDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    getReportDetail(id)
      .then(setReport)
      .catch(() => setError('Report not found or backend not running.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" label="Loading report…" /></div>
  if (error || !report) return (
    <div className="flex flex-col items-center gap-3 py-16">
      <AlertTriangle size={24} className="text-[#EF4444]" />
      <p className="text-[#9CA3AF] text-sm">{error}</p>
      <button onClick={() => navigate('/lab-reports')} className="text-[#0EA5E9] text-sm hover:underline">
        ← Back to reports
      </button>
    </div>
  )

  const categories = [...new Set(report.biomarkers.map(b => b.category))]
  const abnormal = report.biomarkers.filter(b => b.status !== 'normal')
  const normal = report.biomarkers.filter(b => b.status === 'normal')

  return (
    <PageWrapper
      title={report.filename}
      subtitle={`${report.lab_name} · ${report.report_date}`}
      action={
        <button
          onClick={() => navigate('/lab-reports')}
          className="flex items-center gap-1 text-[#9CA3AF] hover:text-[#F9FAFB] text-sm transition-colors"
        >
          <ChevronLeft size={14} /> All reports
        </button>
      }
    >
      <div className="space-y-5">

        {/* Summary strip */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Total Biomarkers', value: String(report.biomarkers.length) },
            { label: 'Outside Range', value: String(abnormal.length), alert: abnormal.length > 0 },
            { label: 'Within Normal', value: String(normal.length) },
          ].map(({ label, value, alert }) => (
            <Card key={label} padding="md">
              <p className="text-[#6B7280] text-xs mb-1">{label}</p>
              <p className={`font-bold text-xl ${alert ? 'text-[#EF4444]' : 'text-[#F9FAFB]'}`}>{value}</p>
            </Card>
          ))}
        </div>

        {/* AI explanation */}
        <Card>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#0EA5E9]/10 border border-[#0EA5E9]/20 flex items-center justify-center shrink-0 mt-0.5">
              <span className="text-[#0EA5E9] text-xs font-bold">AI</span>
            </div>
            <div>
              <p className="text-[#6B7280] text-xs mb-1.5">
                Report Summary · Powered by Qwen
                <span className="ml-2 text-[10px] bg-[#1F2937] border border-[#374151] text-[#9CA3AF] px-1.5 py-0.5 rounded">
                  Mock — Qwen connects in Milestone 5
                </span>
              </p>
              <p className="text-[#F9FAFB] text-sm leading-relaxed">
                Your blood report shows <strong className="text-[#EF4444]">{abnormal.length} result{abnormal.length !== 1 ? 's' : ''} outside the reference ranges</strong> provided on the report.
                {abnormal.length > 0 && (
                  <> Specifically: {abnormal.map(b => b.name).join(', ')}. These findings can have multiple explanations.</>
                )}
                {' '}Your {normal.length} other results are within the reference ranges shown on this report.
              </p>
              <p className="mt-2 text-[#6B7280] text-xs italic">
                This is a rule-based summary for educational purposes only. It does not constitute a medical diagnosis. Consider discussing these results with a qualified healthcare professional.
              </p>
            </div>
          </div>
        </Card>

        {/* Biomarkers by category */}
        {categories.map(cat => (
          <section key={cat}>
            <h3 className="text-[#9CA3AF] text-xs font-medium uppercase tracking-wider mb-2.5">{cat}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {report.biomarkers.filter(b => b.category === cat).map(b => (
                <BiomarkerRow key={b.id} b={b} />
              ))}
            </div>
          </section>
        ))}

        {/* Parsing info + disclaimer */}
        <Card padding="sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <p className="text-[#6B7280] text-xs">
              Extraction method: <span className="text-[#9CA3AF]">{report.parsing_method}</span>
              {' · '}Uploaded: <span className="text-[#9CA3AF]">{report.upload_date}</span>
            </p>
            <p className="text-[#6B7280] text-xs text-right">
              Reference ranges are from the uploaded report. Results are for educational purposes only.
            </p>
          </div>
        </Card>

      </div>
    </PageWrapper>
  )
}
