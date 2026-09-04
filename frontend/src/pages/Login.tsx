import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '../components/ui'
import { useAuthStore } from '../store/authStore'
import { Activity, FlaskConical, MessageCircle } from 'lucide-react'

export function Login() {
  const navigate = useNavigate()
  const { user, loading, login, bootstrapped } = useAuthStore()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (bootstrapped && user) {
      navigate('/dashboard', { replace: true })
    }
  }, [bootstrapped, user, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      navigate('/dashboard', { replace: true })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? 'Login failed. Please check your credentials.'
      setError(msg)
    }
  }

  return (
    <div className="min-h-screen bg-[#0A0F1E] flex flex-col items-center justify-center px-4">
      {/* Logo */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-12 h-12 rounded-2xl bg-[#0EA5E9] flex items-center justify-center shadow-lg shadow-[#0EA5E9]/20">
          <span className="text-white font-bold text-xl">H</span>
        </div>
        <div>
          <h1 className="text-2xl font-bold text-[#F9FAFB]">HealthOS</h1>
          <p className="text-[#9CA3AF] text-sm">Your Personal Health Intelligence Layer</p>
        </div>
      </div>

      {/* Feature pills */}
      <div className="flex flex-wrap justify-center gap-3 mb-8">
        {[
          { icon: FlaskConical, label: 'Lab Report Analysis' },
          { icon: Activity, label: 'Health Priorities' },
          { icon: MessageCircle, label: 'AI Health Assistant' },
        ].map(({ icon: Icon, label }) => (
          <div key={label} className="flex items-center gap-2 bg-[#111827] border border-[#1F2937] rounded-full px-4 py-2">
            <Icon size={14} className="text-[#0EA5E9]" />
            <span className="text-[#9CA3AF] text-sm">{label}</span>
          </div>
        ))}
      </div>

      <div className="w-full max-w-sm bg-[#111827] border border-[#1F2937] rounded-2xl p-6">
        <h2 className="text-xl font-bold text-[#F9FAFB] mb-1">Sign in</h2>
        <p className="text-[#9CA3AF] text-sm mb-6">Welcome back to your health dashboard.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[#9CA3AF] text-xs mb-1.5">Email address</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
              className="w-full bg-[#0A0F1E] border border-[#374151] rounded-lg px-3 py-2.5 text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none focus:border-[#0EA5E9] transition-colors"
            />
          </div>

          <div>
            <label className="block text-[#9CA3AF] text-xs mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="w-full bg-[#0A0F1E] border border-[#374151] rounded-lg px-3 py-2.5 text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none focus:border-[#0EA5E9] transition-colors"
            />
          </div>

          {error && (
            <div className="bg-[#EF4444]/10 border border-[#EF4444]/20 rounded-lg p-3 text-[#EF4444] text-xs">
              {error}
            </div>
          )}

          <Button type="submit" loading={loading} className="w-full">
            Sign in
          </Button>
        </form>

        <p className="mt-5 text-center text-[#9CA3AF] text-xs">
          Don't have an account?{' '}
          <Link to="/register" className="text-[#0EA5E9] hover:underline">Create account</Link>
        </p>
      </div>

      <p className="mt-8 text-[#6B7280] text-xs text-center max-w-sm">
        HealthOS provides health education and information. It does not diagnose diseases or replace professional medical advice.
      </p>
    </div>
  )
}
