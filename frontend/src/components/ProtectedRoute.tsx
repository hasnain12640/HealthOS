import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Spinner } from './ui'

export function ProtectedRoute() {
  const { user, bootstrapped } = useAuthStore()
  const location = useLocation()

  if (!bootstrapped) {
    return (
      <div className="flex items-center justify-center h-screen bg-bg-base">
        <Spinner size="lg" label="Starting HealthOS…" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}
