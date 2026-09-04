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
import { useAuthStore } from './store/authStore'

function AuthBootstrap({ children }: { children: React.ReactNode }) {
  const bootstrap = useAuthStore(state => state.bootstrap)

  useEffect(() => {
    bootstrap()
  }, [bootstrap])

  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthBootstrap>
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
