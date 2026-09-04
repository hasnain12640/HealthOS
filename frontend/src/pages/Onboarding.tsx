import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Button, Spinner } from '../components/ui'
import { createProfile } from '../services/profileService'
import { useAuthStore } from '../store/authStore'
import { User, MapPin, Ruler, ChevronRight } from 'lucide-react'

const steps = ['Basic Info', 'Body Metrics', 'Lifestyle', 'Done']

export function Onboarding() {
  const [step, setStep] = useState(0)
  const navigate = useNavigate()
  const { user, profile, setProfile, bootstrapped } = useAuthStore()

  const [form, setForm] = useState({
    user_name: '',
    age: '',
    sex: 'male',
    city: '',
    height_cm: '',
    weight_kg: '',
    blood_group: 'A+',
    language: 'en',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (bootstrapped && !user) {
      navigate('/login', { replace: true })
      return
    }
    if (bootstrapped && profile) {
      navigate('/dashboard', { replace: true })
    }
  }, [bootstrapped, user, profile, navigate])

  const update = (key: keyof typeof form, value: string) => {
    setForm(f => ({ ...f, [key]: value }))
    setError('')
  }

  const validateBasic = () => {
    if (!form.user_name.trim()) return 'Please enter your full name.'
    if (!form.age || Number(form.age) <= 0) return 'Please enter a valid age.'
    if (!form.city.trim()) return 'Please enter your city.'
    return ''
  }

  const validateBody = () => {
    if (!form.height_cm || Number(form.height_cm) <= 0) return 'Please enter a valid height.'
    if (!form.weight_kg || Number(form.weight_kg) <= 0) return 'Please enter a valid weight.'
    return ''
  }

  const handleNext = () => {
    if (step === 0) {
      const err = validateBasic()
      if (err) { setError(err); return }
    }
    if (step === 1) {
      const err = validateBody()
      if (err) { setError(err); return }
    }
    setStep(s => s + 1)
  }

  const handleCreateProfile = async () => {
    setSubmitting(true)
    setError('')
    try {
      const profile = await createProfile({
        user_name: form.user_name.trim(),
        age: Number(form.age),
        sex: form.sex,
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        blood_group: form.blood_group,
        city: form.city.trim(),
        language: form.language,
      })
      setProfile(profile)
      setStep(3)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? 'Could not create profile. Please try again.'
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  if (!bootstrapped) {
    return (
      <div className="min-h-screen bg-[#0A0F1E] flex items-center justify-center">
        <Spinner size="lg" label="Loading…" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0A0F1E] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Progress */}
        <div className="flex items-center justify-between mb-8">
          {steps.map((label, i) => (
            <div key={label} className="flex items-center gap-1">
              <div className={[
                'w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold',
                i <= step ? 'bg-[#0EA5E9] text-white' : 'bg-[#1F2937] text-[#6B7280]',
              ].join(' ')}>
                {i + 1}
              </div>
              <span className={`text-xs hidden sm:block ${i <= step ? 'text-[#F9FAFB]' : 'text-[#6B7280]'}`}>
                {label}
              </span>
              {i < steps.length - 1 && <div className="w-8 h-px bg-[#1F2937] mx-1" />}
            </div>
          ))}
        </div>

        <Card>
          {step === 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <User size={18} className="text-[#0EA5E9]" />
                <h2 className="text-[#F9FAFB] font-semibold">Basic Information</h2>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Full Name</label>
                  <input
                    type="text"
                    value={form.user_name}
                    onChange={e => update('user_name', e.target.value)}
                    placeholder="e.g. Ahmed Khan"
                    className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none focus:border-[#0EA5E9] transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Age</label>
                  <input
                    type="number"
                    value={form.age}
                    onChange={e => update('age', e.target.value)}
                    placeholder="e.g. 34"
                    className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none focus:border-[#0EA5E9] transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Sex</label>
                  <select
                    value={form.sex}
                    onChange={e => update('sex', e.target.value)}
                    className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] outline-none focus:border-[#0EA5E9] transition-colors"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">City</label>
                  <div className="relative">
                    <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6B7280]" />
                    <input
                      type="text"
                      value={form.city}
                      onChange={e => update('city', e.target.value)}
                      placeholder="e.g. Lahore, Karachi, Islamabad"
                      className="w-full bg-[#1F2937] border border-[#374151] rounded-lg pl-8 pr-3 py-2 text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none focus:border-[#0EA5E9] transition-colors"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <Ruler size={18} className="text-[#0EA5E9]" />
                <h2 className="text-[#F9FAFB] font-semibold">Body Metrics</h2>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Height (cm)</label>
                  <input
                    type="number"
                    value={form.height_cm}
                    onChange={e => update('height_cm', e.target.value)}
                    placeholder="e.g. 172"
                    className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none focus:border-[#0EA5E9] transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Weight (kg)</label>
                  <input
                    type="number"
                    value={form.weight_kg}
                    onChange={e => update('weight_kg', e.target.value)}
                    placeholder="e.g. 82"
                    className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none focus:border-[#0EA5E9] transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Blood Group</label>
                  <select
                    value={form.blood_group}
                    onChange={e => update('blood_group', e.target.value)}
                    className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] outline-none focus:border-[#0EA5E9] transition-colors"
                  >
                    {['A+', 'A−', 'B+', 'B−', 'AB+', 'AB−', 'O+', 'O−'].map(g => (
                      <option key={g} value={g}>{g}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-[#F9FAFB] font-semibold mb-4">Lifestyle Snapshot</h2>
              <p className="text-[#9CA3AF] text-sm">This helps HealthOS personalize your priorities and plan.</p>
              <div className="space-y-3">
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Average sleep per night (hours)</label>
                  <input type="number" placeholder="e.g. 7" className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none focus:border-[#0EA5E9] transition-colors" />
                </div>
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Daily water intake (glasses)</label>
                  <input type="number" placeholder="e.g. 8" className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none focus:border-[#0EA5E9] transition-colors" />
                </div>
                <div>
                  <label className="block text-[#9CA3AF] text-xs mb-1">Activity level</label>
                  <select className="w-full bg-[#1F2937] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] outline-none focus:border-[#0EA5E9] transition-colors">
                    <option>Sedentary (mostly sitting)</option>
                    <option>Light (walking 1–3 days/week)</option>
                    <option>Moderate (exercise 3–5 days/week)</option>
                    <option>Active (exercise 6–7 days/week)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="text-center py-4 space-y-4">
              <div className="w-14 h-14 rounded-full bg-[#10B981]/10 border border-[#10B981]/20 flex items-center justify-center mx-auto">
                <span className="text-[#10B981] text-2xl">✓</span>
              </div>
              <h2 className="text-[#F9FAFB] font-semibold text-lg">Profile Created</h2>
              <p className="text-[#9CA3AF] text-sm">Your HealthOS profile is ready. You can now upload lab reports and start tracking.</p>
            </div>
          )}

          {error && (
            <div className="mt-4 bg-[#EF4444]/10 border border-[#EF4444]/20 rounded-lg p-3 text-[#EF4444] text-xs">
              {error}
            </div>
          )}

          <div className="flex justify-between mt-6">
            {step > 0 && step < 3 && (
              <Button variant="ghost" onClick={() => setStep(s => s - 1)}>Back</Button>
            )}
            <div className="ml-auto">
              {step < 2 && (
                <Button onClick={handleNext}>
                  Continue <ChevronRight size={14} />
                </Button>
              )}
              {step === 2 && (
                <Button onClick={handleCreateProfile} loading={submitting}>
                  Create Profile
                </Button>
              )}
              {step === 3 && (
                <Button onClick={() => navigate('/dashboard')}>
                  Go to Dashboard <ChevronRight size={14} />
                </Button>
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
