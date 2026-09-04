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
      <Card><p className="text-[#EF4444] text-sm text-center py-4">{error}</p></Card>
    </PageWrapper>
  )

  if (!profile || !bodyMetrics) return (
    <PageWrapper title="Health Profile" subtitle="Your personal health information">
      <div className="flex justify-center py-12"><Spinner size="lg" /></div>
    </PageWrapper>
  )

  const initials = profile.user_name.split(' ').map(n => n[0]).join('')
  const bmiColor = bodyMetrics.category === 'Normal weight' ? '#10B981'
    : bodyMetrics.category === 'Underweight' ? '#F59E0B'
    : bodyMetrics.severity === 'medium' ? '#EF4444' : '#F59E0B'

  return (
    <PageWrapper title="Health Profile" subtitle="Your personal health information">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-full bg-[#0EA5E9]/10 border border-[#0EA5E9]/20 flex items-center justify-center">
              <span className="text-[#0EA5E9] font-bold">{initials}</span>
            </div>
            <div>
              <h2 className="text-[#F9FAFB] font-semibold">{profile.user_name}</h2>
              <p className="text-[#9CA3AF] text-sm flex items-center gap-1">
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
              <div key={label} className="bg-[#1F2937] rounded-lg p-3">
                <p className="text-[#6B7280] text-xs mb-1">{label}</p>
                <p className="text-[#F9FAFB] text-sm font-medium">{value}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h3 className="text-[#F9FAFB] font-semibold mb-4 flex items-center gap-2">
            <Ruler size={16} className="text-[#0EA5E9]" /> Body Metrics
          </h3>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div className="bg-[#1F2937] rounded-lg p-3 text-center">
              <p className="text-[#6B7280] text-xs mb-1">Height</p>
              <p className="text-[#F9FAFB] font-semibold">{profile.height_cm} cm</p>
            </div>
            <div className="bg-[#1F2937] rounded-lg p-3 text-center">
              <p className="text-[#6B7280] text-xs mb-1">Weight</p>
              <p className="text-[#F9FAFB] font-semibold">{profile.weight_kg} kg</p>
            </div>
            <div className="bg-[#1F2937] rounded-lg p-3 text-center">
              <p className="text-[#6B7280] text-xs mb-1">BMI</p>
              <p className="font-semibold" style={{ color: bmiColor }}>{bodyMetrics.bmi}</p>
            </div>
          </div>
          <div className="bg-[#1F2937] rounded-lg p-3 flex items-center justify-between">
            <span className="text-[#9CA3AF] text-sm">Classification</span>
            <span className="font-medium text-sm" style={{ color: bmiColor }}>{bodyMetrics.category}</span>
          </div>
          <p className="text-[#9CA3AF] text-xs mt-3">
            BMI is a general screening metric. It does not diagnose any health condition.
          </p>
        </Card>
      </div>
    </PageWrapper>
  )
}
