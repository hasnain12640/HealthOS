import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui'
import { Activity, FlaskConical, MessageCircle } from 'lucide-react'

export function Welcome() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-bg-base flex flex-col items-center justify-center px-4">
      {/* Logo */}
      <div className="flex items-center gap-3 mb-10">
        <div className="w-12 h-12 rounded-2xl bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
          <span className="text-white font-bold text-xl">H</span>
        </div>
        <div>
          <h1 className="text-2xl font-bold text-text-primary">HealthOS</h1>
          <p className="text-text-secondary text-sm">Your Personal Health Intelligence Layer</p>
        </div>
      </div>

      {/* Hero */}
      <div className="text-center max-w-lg mb-10">
        <h2 className="text-3xl font-bold text-text-primary mb-3 leading-tight">
          Understand your health<br />
          <span className="text-primary">like never before</span>
        </h2>
        <p className="text-text-secondary text-base leading-relaxed">
          Upload your lab reports. Track your nutrition, sleep, and hydration.
          Get personalized AI-powered insights in plain language — tailored for Pakistan.
        </p>
      </div>

      {/* Feature pills */}
      <div className="flex flex-wrap justify-center gap-3 mb-10">
        {[
          { icon: FlaskConical, label: 'Lab Report Analysis' },
          { icon: Activity, label: 'Health Priorities' },
          { icon: MessageCircle, label: 'AI Health Assistant' },
        ].map(({ icon: Icon, label }) => (
          <div key={label} className="flex items-center gap-2 bg-bg-surface border border-border rounded-full px-4 py-2">
            <Icon size={14} className="text-primary" />
            <span className="text-text-secondary text-sm">{label}</span>
          </div>
        ))}
      </div>

      {/* CTA */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Button size="lg" onClick={() => navigate('/login')}>
          Sign In
        </Button>
        <Button size="lg" variant="secondary" onClick={() => navigate('/register')}>
          Create Account
        </Button>
      </div>

      {/* Safety disclaimer */}
      <p className="mt-8 text-text-muted text-xs text-center max-w-sm">
        HealthOS provides health education and information. It does not diagnose diseases or replace professional medical advice.
      </p>
    </div>
  )
}
