import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { AppShell } from './components/layout/AppShell'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Welcome } from './pages/Welcome'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { Onboarding } from './pages/Onboarding'
import { HealthProfile } from './pages/HealthProfile'
import { Dashboard } from './pages/Dashboard'
import { LabReports } from './pages/LabReports'
import { LabReportDetail } from './pages/LabReportDetail'
import { HealthTimeline } from './pages/HealthTimeline'
import { Nutrition } from './pages/Nutrition'
import { Hydration } from './pages/Hydration'
import { ActivityPage } from './pages/Activity'
import { AIAssistant } from './pages/AIAssistant'
import { SevenDayPlan } from './pages/SevenDayPlan'
import { Settings } from './pages/Settings'
import { Wearables } from './pages/Wearables'
import { WomensHealth } from './pages/WomensHealth'
import { useAuthStore } from './store/authStore'
import { useSettingsStore } from './store/settingsStore'

function AuthBootstrap({ children }: { children: React.ReactNode }) {
  const bootstrap = useAuthStore(state => state.bootstrap)

  useEffect(() => {
    bootstrap()
  }, [bootstrap])

  return <>{children}</>
}

function ThemeSync() {
  const theme = useSettingsStore(s => s.theme)
  const language = useSettingsStore(s => s.language)

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('light', theme === 'light')
    root.setAttribute('dir', language === 'ur' ? 'rtl' : 'ltr')
    root.setAttribute('lang', language)
  }, [theme, language])

  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthBootstrap>
        <ThemeSync />
        <Routes>
          {/* Public pages — no app shell */}
          <Route path="/" element={<Welcome />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Onboarding is public-ish but will redirect logged-out users via ProtectedRoute */}
          <Route element={<ProtectedRoute />}>
            <Route path="/onboarding" element={<Onboarding />} />
          </Route>

          {/* Main app — with sidebar + topbar */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/profile" element={<HealthProfile />} />
              <Route path="/lab-reports" element={<LabReports />} />
              <Route path="/lab-reports/:id" element={<LabReportDetail />} />
              <Route path="/timeline" element={<HealthTimeline />} />
              <Route path="/nutrition" element={<Nutrition />} />
              <Route path="/hydration" element={<Hydration />} />
              <Route path="/activity" element={<ActivityPage />} />
              <Route path="/assistant" element={<AIAssistant />} />
              <Route path="/plan" element={<SevenDayPlan />} />
              <Route path="/wearables" element={<Wearables />} />
              <Route path="/womens-health" element={<WomensHealth />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthBootstrap>
    </BrowserRouter>
  )
}
