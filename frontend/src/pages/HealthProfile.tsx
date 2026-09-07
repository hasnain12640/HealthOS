import { useEffect, useState } from 'react'
import { PageWrapper, Card, Spinner } from '../components/ui'
import { getAnalysis, type BodyMetrics } from '../services/analysisService'
import { getProfile, type ProfileData } from '../services/profileService'
import { MapPin, Ruler } from 'lucide-react'

export function HealthProfile() {
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [bodyMetrics, setBodyMetrics] = useState<BodyMetrics | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      getProfile(),
      getAnalysis(),
    ])
      .then(([profile, analysis]) => {
        setProfile(profile)
        setBodyMetrics(analysis.body_metrics)
      })
      .catch(() => setError('Could not load profile. Is the backend running?'))
  }, [])

  if (error) return (
    <PageWrapper title="Health Profile" subtitle="Your personal health information">
      <Card><p className="text-danger text-sm text-center py-4">{error}</p></Card>
    </PageWrapper>
  )

  if (!profile || !bodyMetrics) return (
    <PageWrapper title="Health Profile" subtitle="Your personal health information">
      <div className="flex justify-center py-12"><Spinner size="lg" /></div>
    </PageWrapper>
  )

  const initials = profile.user_name.split(' ').map(n => n[0]).join('')
  const bmiColor = bodyMetrics.category === 'Normal weight' ? 'var(--color-accent)'
    : bodyMetrics.category === 'Underweight' ? 'var(--color-warning)'
    : bodyMetrics.severity === 'medium' ? 'var(--color-danger)' : 'var(--color-warning)'

  return (
    <PageWrapper title="Health Profile" subtitle="Your personal health information">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
              <span className="text-primary font-bold">{initials}</span>
            </div>
            <div>
              <h2 className="text-text-primary font-semibold">{profile.user_name}</h2>
              <p className="text-text-secondary text-sm flex items-center gap-1">
                <MapPin size={12} /> {profile.city}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Age', value: `${profile.age} years` },
              { label: 'Sex', value: profile.sex === 'male' ? 'Male' : 'Female' },
              { label: 'Blood Group', value: profile.blood_group },
              { label: 'Language', value: profile.language === 'en' ? 'English' : 'اردو' },
            ].map(({ label, value }) => (
              <div key={label} className="bg-bg-elevated rounded-lg p-3">
                <p className="text-text-muted text-xs mb-1">{label}</p>
                <p className="text-text-primary text-sm font-medium">{value}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h3 className="text-text-primary font-semibold mb-4 flex items-center gap-2">
            <Ruler size={16} className="text-primary" /> Body Metrics
          </h3>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div className="bg-bg-elevated rounded-lg p-3 text-center">
              <p className="text-text-muted text-xs mb-1">Height</p>
              <p className="text-text-primary font-semibold">{profile.height_cm} cm</p>
            </div>
            <div className="bg-bg-elevated rounded-lg p-3 text-center">
              <p className="text-text-muted text-xs mb-1">Weight</p>
              <p className="text-text-primary font-semibold">{profile.weight_kg} kg</p>
            </div>
            <div className="bg-bg-elevated rounded-lg p-3 text-center">
              <p className="text-text-muted text-xs mb-1">BMI</p>
              <p className="font-semibold" style={{ color: bmiColor }}>{bodyMetrics.bmi}</p>
            </div>
          </div>
          <div className="bg-bg-elevated rounded-lg p-3 flex items-center justify-between">
            <span className="text-text-secondary text-sm">Classification</span>
            <span className="font-medium text-sm" style={{ color: bmiColor }}>{bodyMetrics.category}</span>
          </div>
          <p className="text-text-secondary text-xs mt-3">
            BMI is a general screening metric. It does not diagnose any health condition.
          </p>
        </Card>
      </div>
    </PageWrapper>
  )
}
