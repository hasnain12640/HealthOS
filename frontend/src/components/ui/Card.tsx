import React from 'react'

interface CardProps {
  children: React.ReactNode
  className?: string
  padding?: 'sm' | 'md' | 'lg' | 'none'
  onClick?: () => void
}

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-6',
}

export function Card({ children, className = '', padding = 'md', onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={[
        'bg-[#111827] border border-[#1F2937] rounded-xl',
        paddingStyles[padding],
        onClick ? 'cursor-pointer hover:border-[#374151] transition-colors' : '',
        className,
      ].join(' ')}
    >
      {children}
    </div>
  )
}

interface CardHeaderProps {
  title: string
  subtitle?: string
  action?: React.ReactNode
}

export function CardHeader({ title, subtitle, action }: CardHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="text-[#F9FAFB] font-semibold text-sm">{title}</h3>
        {subtitle && <p className="text-[#9CA3AF] text-xs mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}
