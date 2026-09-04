import api from './api'

export interface BiomarkerData {
  id: string
  name: string
  value: number
  unit: string
  reference_low: number | null
  reference_high: number | null
  status: 'normal' | 'low' | 'high' | 'critical'
  category: string
}

export interface ReportDetail {
  id: string
  profile_id: string
  filename: string
  lab_name: string
  report_date: string
  parsing_method: string
  upload_date: string
  biomarkers: BiomarkerData[]
}

export interface ReportSummary {
  id: string
  filename: string
  lab_name: string
  report_date: string
  upload_date: string
  total_biomarkers: number
  abnormal_count: number
}

export async function listReports(): Promise<ReportSummary[]> {
  const res = await api.get<ReportSummary[]>('/lab')
  return res.data
}

export async function getReportDetail(reportId: string): Promise<ReportDetail> {
  const res = await api.get<ReportDetail>(`/lab/detail/${reportId}`)
  return res.data
}

export async function uploadReport(
  file: File,
  labName: string,
  reportDate: string,
): Promise<ReportDetail> {
  const form = new FormData()
  form.append('lab_name', labName)
  form.append('report_date', reportDate)
  form.append('file', file)
  const res = await api.post<ReportDetail>('/lab/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}
