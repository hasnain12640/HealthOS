import { useEffect, useState } from 'react'
import { Card, Button, Badge } from '../ui'
import {
  getBiomarkerCatalog,
  createManualReport,
  type CatalogItem,
  type ManualBiomarkerInput,
} from '../../services/labService'
import { FlaskConical, X, AlertTriangle, CheckCircle2, Plus, Trash2 } from 'lucide-react'

interface ManualEntryModalProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

interface Row {
  id: number
  selectedName: string
  value: string
}

const EMPTY_ROW: Row = { id: 0, selectedName: '', value: '' }

export function ManualEntryModal({ open, onClose, onSuccess }: ManualEntryModalProps) {
  const [catalog, setCatalog] = useState<CatalogItem[]>([])
  const [labName, setLabName] = useState('')
  const [reportDate, setReportDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [rows, setRows] = useState<Row[]>([{ ...EMPTY_ROW, id: Date.now() }])
  const [loading, setLoading] = useState(false)
  const [catalogLoading, setCatalogLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    setCatalogLoading(true)
    setError(null)
    setSuccess(null)
    getBiomarkerCatalog()
      .then(setCatalog)
      .catch(() => setError('Could not load biomarker catalog. Please try again.'))
      .finally(() => setCatalogLoading(false))
  }, [open])

  if (!open) return null

  const findCatalogItem = (name: string) => catalog.find(c => c.name === name)

  const handleAddRow = () => {
    setRows(prev => [...prev, { ...EMPTY_ROW, id: Date.now() + prev.length }])
  }

  const handleRemoveRow = (id: number) => {
    setRows(prev => (prev.length <= 1 ? prev : prev.filter(r => r.id !== id)))
  }

  const updateRow = (id: number, patch: Partial<Row>) => {
    setRows(prev => prev.map(r => (r.id === id ? { ...r, ...patch } : r)))
  }

  const validate = (): ManualBiomarkerInput[] | null => {
    const biomarkers: ManualBiomarkerInput[] = []
    for (const row of rows) {
      const item = findCatalogItem(row.selectedName)
      if (!item) {
        setError('Please select a biomarker for every row.')
        return null
      }
      const value = Number(row.value)
      if (!Number.isFinite(value)) {
        setError(`Enter a numeric value for ${item.name}.`)
        return null
      }
      biomarkers.push({
        name: item.name,
        value,
        unit: item.unit,
        reference_low: item.reference_low,
        reference_high: item.reference_high,
        category: item.category,
      })
    }
    if (!reportDate) {
      setError('Please select a report date.')
      return null
    }
    return biomarkers
  }

  const handleSubmit = async () => {
    const biomarkers = validate()
    if (!biomarkers) return

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await createManualReport({
        lab_name: labName || 'Manual Entry',
        report_date: reportDate,
        biomarkers,
      })
      setSuccess(`${result.biomarkers.length} biomarker(s) saved successfully.`)
      onSuccess()
      setTimeout(() => {
        setLabName('')
        setRows([{ ...EMPTY_ROW, id: Date.now() }])
        onClose()
      }, 1200)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Could not save manual report. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto mt-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
              <FlaskConical size={16} className="text-primary" />
            </div>
            <div>
              <h3 className="text-text-primary font-semibold text-sm">Manual Lab Entry</h3>
              <p className="text-text-secondary text-xs">Add biomarkers one at a time using the catalog.</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary transition-colors"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-text-secondary text-xs mb-1">Lab Name</label>
              <input
                type="text"
                value={labName}
                onChange={e => setLabName(e.target.value)}
                placeholder="e.g. Chughtai Lab"
                className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-primary transition-colors"
              />
            </div>
            <div>
              <label className="block text-text-secondary text-xs mb-1">Report Date</label>
              <input
                type="date"
                value={reportDate}
                onChange={e => setReportDate(e.target.value)}
                className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-primary transition-colors"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-text-secondary text-xs">Biomarkers</label>
              <button
                onClick={handleAddRow}
                className="inline-flex items-center gap-1 text-xs text-primary hover:text-primary-light transition-colors"
              >
                <Plus size={13} /> Add biomarker
              </button>
            </div>

            {catalogLoading ? (
              <p className="text-text-muted text-xs py-4 text-center">Loading catalog…</p>
            ) : (
              <div className="space-y-2">
                {rows.map((row) => {
                  const item = findCatalogItem(row.selectedName)
                  return (
                    <div
                      key={row.id}
                      className="grid grid-cols-[1fr_6rem_2.5rem] sm:grid-cols-[1fr_8rem_2.5rem] gap-2 items-end rounded-lg border border-border-subtle bg-bg-base/60 p-2.5"
                    >
                      <div>
                        <label className="block text-text-muted text-[10px] mb-1">Biomarker</label>
                        <select
                          value={row.selectedName}
                          onChange={e => updateRow(row.id, { selectedName: e.target.value })}
                          className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-2 py-2 text-xs text-text-primary outline-none focus:border-primary"
                        >
                          <option value="">Select…</option>
                          {catalog.map(c => (
                            <option key={c.name} value={c.name}>{c.name}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-text-muted text-[10px] mb-1">
                          Value {item ? `(${item.unit})` : ''}
                        </label>
                        <input
                          type="number"
                          step="any"
                          value={row.value}
                          onChange={e => updateRow(row.id, { value: e.target.value })}
                          placeholder="0.0"
                          className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-2 py-2 text-xs text-text-primary placeholder-text-muted outline-none focus:border-primary"
                        />
                      </div>
                      <button
                        onClick={() => handleRemoveRow(row.id)}
                        disabled={rows.length <= 1}
                        className="flex items-center justify-center h-9 rounded-lg border border-border-subtle text-text-muted hover:text-danger hover:border-danger/30 transition-colors disabled:opacity-30"
                        aria-label="Remove row"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {rows.some(r => r.selectedName) && (
            <div className="flex flex-wrap gap-1.5">
              {rows
                .map(r => findCatalogItem(r.selectedName))
                .filter(Boolean)
                .map(item => (
                  <Badge
                    key={item!.name}
                    label={`${item!.name} ${item!.reference_low != null || item!.reference_high != null
                      ? `(${item!.reference_low ?? '—'}–${item!.reference_high ?? '—'} ${item!.unit})`
                      : `(${item!.unit})`}`}
                    variant="info"
                    size="sm"
                  />
                ))}
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 bg-danger/10 border border-danger/20 rounded-lg p-3">
              <AlertTriangle size={14} className="text-danger shrink-0 mt-0.5" />
              <p className="text-danger text-xs">{error}</p>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 bg-accent/10 border border-accent/20 rounded-lg p-3">
              <CheckCircle2 size={14} className="text-accent" />
              <p className="text-accent text-xs">{success}</p>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" size="sm" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleSubmit} loading={loading} disabled={catalogLoading}>
              Save Report
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
