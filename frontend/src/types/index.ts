export interface HealthProfile {
  id: string
  userName: string
  age: number
  sex: 'male' | 'female'
  heightCm: number
  weightKg: number
  bloodGroup: string
  city: string
  language: 'en' | 'ur'
  createdAt: string
}

export interface Biomarker {
  id: string
  reportId: string
  name: string
  value: number
  unit: string
  referenceLow: number | null
  referenceHigh: number | null
  status: 'normal' | 'low' | 'high' | 'critical'
  category: 'CBC' | 'metabolic' | 'lipid' | 'thyroid' | 'vitamin' | 'other'
}

export interface LabReport {
  id: string
  profileId: string
  filename: string
  labName: string
  reportDate: string
  uploadDate: string
  biomarkers: Biomarker[]
}

export interface NutritionLog {
  id: string
  profileId: string
  date: string
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  foodName: string
  quantityG: number
  calories: number
  proteinG: number
  carbsG: number
  fatG: number
  isPakistaniFood: boolean
}

export interface HydrationLog {
  id: string
  profileId: string
  date: string
  amountMl: number
  source: 'water' | 'lassi' | 'tea' | 'juice' | 'other'
}

export interface ActivityLog {
  id: string
  profileId: string
  date: string
  activityType: string
  durationMin: number
  steps: number
  notes: string
}

export interface SleepLog {
  id: string
  profileId: string
  date: string
  hoursSlept: number
  quality: 1 | 2 | 3 | 4 | 5
}

export interface TimelineEvent {
  id: string
  profileId: string
  date: string
  eventType: 'lab' | 'nutrition' | 'hydration' | 'ai_insight' | 'plan' | 'activity' | 'wearable' | 'cycle' | 'cycle_symptom'
  title: string
  description: string
  isAIGenerated: boolean
}

export interface HealthPriority {
  id: string
  title: string
  observedData: string
  aiInterpretation: string
  suggestedAction: string
  severity: 'low' | 'medium' | 'high'
  category: string
}

export interface SevenDayPlan {
  generatedAt: string
  days: DayPlan[]
}

export interface DayPlan {
  day: number
  dayLabel: string
  nutrition: string[]
  hydration: string
  activity: string
  sleep: string
  focus: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export type InsightDomain = 'labs' | 'hydration' | 'sleep' | 'activity' | 'nutrition' | 'wearable' | 'cycle'

export interface ObservedDataItem {
  domain: InsightDomain
  observation: string
  value: string
}

export interface CrossDomainConnection {
  domains: InsightDomain[]
  relationship: string
  explanation: string
}

export interface InsightPriority {
  title: string
  rationale: string
  suggested_action: string
  related_domains: InsightDomain[]
  urgency: 'high' | 'medium' | 'low'
}

export interface StructuredInsight {
  headline: string
  summary: string
  observed_data: ObservedDataItem[]
  cross_domain_connections: CrossDomainConnection[]
  priorities: InsightPriority[]
  safety_note: string
}
