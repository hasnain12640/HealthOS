import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Button, Spinner } from '../components/ui'
import { createProfile } from '../services/profileService'
import { useAuthStore } from '../store/authStore'
import { User, MapPin, Ruler, ChevronRight } from 'lucide-react'

const steps = ['Basic Info', 'Body Metrics']

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
    const err = validateBody()
    if (err) { setError(err); return }
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
      setStep(2)
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
      <div className="min-h-screen bg-bg-base flex items-center justify-center">
        <Spinner size="lg" label="Loading…" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg-base flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Progress */}
        {step < steps.length && (
          <div className="flex items-center justify-between mb-8">
            {steps.map((label, i) => (
              <div key={label} className="flex items-center gap-1">
                <div className={[
                  'w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold',
                  i <= step ? 'bg-primary text-white' : 'bg-bg-elevated text-text-muted',
                ].join(' ')}>
                  {i + 1}
                </div>
                <span className={`text-xs hidden sm:block ${i <= step ? 'text-text-primary' : 'text-text-muted'}`}>
                  {label}
                </span>
                {i < steps.length - 1 && <div className="w-8 h-px bg-border mx-1" />}
              </div>
            ))}
          </div>
        )}

        <Card>
          {step === 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <User size={18} className="text-primary" />
                <h2 className="text-text-primary font-semibold">Basic Information</h2>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="block text-text-secondary text-xs mb-1">Full Name</label>
                  <input
                    type="text"
                    value={form.user_name}
                    onChange={e => update('user_name', e.target.value)}
                    placeholder="e.g. Ahmed Khan"
                    className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-text-secondary text-xs mb-1">Age</label>
                  <input
                    type="number"
                    value={form.age}
                    onChange={e => update('age', e.target.value)}
                    placeholder="e.g. 34"
                    className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-text-secondary text-xs mb-1">Sex</label>
                  <select
                    value={form.sex}
                    onChange={e => update('sex', e.target.value)}
                    className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-primary transition-colors"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>
                <div>
                  <label className="block text-text-secondary text-xs mb-1">City</label>
                  <div className="relative">
                    <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                    <input
                      type="text"
                      value={form.city}
                      onChange={e => update('city', e.target.value)}
                      placeholder="e.g. Lahore, Karachi, Islamabad"
                      className="w-full bg-bg-elevated border border-border-subtle rounded-lg pl-8 pr-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-primary transition-colors"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <Ruler size={18} className="text-primary" />
                <h2 className="text-text-primary font-semibold">Body Metrics</h2>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="block text-text-secondary text-xs mb-1">Height (cm)</label>
                  <input
                    type="number"
                    value={form.height_cm}
                    onChange={e => update('height_cm', e.target.value)}
                    placeholder="e.g. 172"
                    className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-text-secondary text-xs mb-1">Weight (kg)</label>
                  <input
                    type="number"
                    value={form.weight_kg}
                    onChange={e => update('weight_kg', e.target.value)}
                    placeholder="e.g. 82"
                    className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-text-secondary text-xs mb-1">Blood Group</label>
                  <select
                    value={form.blood_group}
                    onChange={e => update('blood_group', e.target.value)}
                    className="w-full bg-bg-elevated border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-primary transition-colors"
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
            <div className="text-center py-4 space-y-4">
              <div className="w-14 h-14 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto">
                <span className="text-accent text-2xl">✓</span>
              </div>
              <h2 className="text-text-primary font-semibold text-lg">Profile Created</h2>
              <p className="text-text-secondary text-sm">Your HealthOS profile is ready. You can now upload lab reports and start tracking.</p>
            </div>
          )}

          {error && (
            <div className="mt-4 bg-danger/10 border border-danger/20 rounded-lg p-3 text-danger text-xs">
              {error}
            </div>
          )}

          <div className="flex justify-between mt-6">
            {step > 0 && step < 2 && (
              <Button variant="ghost" onClick={() => setStep(s => s - 1)}>Back</Button>
            )}
            <div className="ml-auto">
              {step === 0 && (
                <Button onClick={handleNext}>
                  Continue <ChevronRight size={14} />
                </Button>
              )}
              {step === 1 && (
                <Button onClick={handleCreateProfile} loading={submitting}>
                  Create Profile
                </Button>
              )}
              {step === 2 && (
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
