import { useState } from 'react'
import { PageWrapper, Card } from '../components/ui'
import { Globe, Moon } from 'lucide-react'

export function Settings() {
  const [language] = useState('en')

  return (
    <PageWrapper title="Settings" subtitle="Preferences and application configuration">
      <div className="space-y-4 max-w-lg">
        <Card>
          <h3 className="text-[#F9FAFB] font-semibold text-sm mb-3 flex items-center gap-2">
            <Globe size={14} className="text-[#0EA5E9]" /> Language
          </h3>
          <div className="flex gap-2">
            {[
              { value: 'en', label: 'English' },
              { value: 'ur', label: 'اردو' },
            ].map(({ value, label }) => (
              <button
                key={value}
                className={[
                  'px-4 py-2 rounded-lg border text-sm font-medium transition-colors',
                  language === value
                    ? 'bg-[#0EA5E9]/10 border-[#0EA5E9] text-[#0EA5E9]'
                    : 'bg-[#1F2937] border-[#374151] text-[#9CA3AF] hover:border-[#0EA5E9]',
                ].join(' ')}
              >
                {label}
              </button>
            ))}
          </div>
          <p className="text-[#6B7280] text-xs mt-2">Urdu language support is coming in a future milestone.</p>
        </Card>

        <Card>
          <h3 className="text-[#F9FAFB] font-semibold text-sm mb-3 flex items-center gap-2">
            <Moon size={14} className="text-[#0EA5E9]" /> Appearance
          </h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[#F9FAFB] text-sm">Dark Mode</p>
              <p className="text-[#6B7280] text-xs">HealthOS uses dark mode by default</p>
            </div>
            <div className="w-10 h-5 rounded-full bg-[#0EA5E9] flex items-center justify-end px-0.5">
              <div className="w-4 h-4 rounded-full bg-white" />
            </div>
          </div>
        </Card>

        <Card>
          <h3 className="text-[#F9FAFB] font-semibold text-sm mb-3">AI Provider</h3>
          <div className="bg-[#1F2937] rounded-lg p-3">
            <p className="text-[#9CA3AF] text-xs mb-1">Current Provider</p>
            <p className="text-[#F9FAFB] text-sm font-medium">Qwen (Alibaba Cloud)</p>
            <p className="text-[#6B7280] text-xs mt-1">Configured via environment variable. Mock mode active for demo.</p>
          </div>
        </Card>

        <Card padding="sm">
          <p className="text-[#6B7280] text-xs text-center">
            HealthOS v0.7.0-milestone7 · Alibaba Cloud AI Hackathon Pakistan 2026
          </p>
        </Card>
      </div>
    </PageWrapper>
  )
}
