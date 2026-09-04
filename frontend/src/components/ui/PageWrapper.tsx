import React from 'react'

interface PageWrapperProps {
  title: string
  subtitle?: string
  action?: React.ReactNode
  children: React.ReactNode
}

export function PageWrapper({ title, subtitle, action, children }: PageWrapperProps) {
  return (
    <div className="flex flex-col min-h-full">
      {/* Page header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-[#F9FAFB]">{title}</h1>
          {subtitle && <p className="text-[#9CA3AF] text-sm mt-1">{subtitle}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>

      {/* Page content */}
      <div className="flex-1">
        {children}
      </div>
    </div>
  )
}
