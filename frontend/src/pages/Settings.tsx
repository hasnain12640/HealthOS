import { PageWrapper, Card } from '../components/ui'
import { Globe, Moon, Sun, Watch, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useSettingsStore } from '../store/settingsStore'
import { useT } from '../i18n/useT'

export function Settings() {
  const { language, theme, setLanguage, toggleTheme } = useSettingsStore()
  const t = useT()
  const navigate = useNavigate()

  return (
    <PageWrapper title={t['settings.title']} subtitle={t['settings.subtitle']}>
      <div className="space-y-4 max-w-lg">
        <Card>
          <h3 className="text-text-primary font-semibold text-sm mb-3 flex items-center gap-2">
            <Globe size={14} className="text-primary" /> {t['settings.language']}
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => setLanguage('en')}
              className={[
                'px-4 py-2 rounded-lg border text-sm font-medium transition-colors',
                language === 'en'
                  ? 'bg-primary/10 border-primary text-primary'
                  : 'bg-bg-elevated border-border-subtle text-text-secondary hover:border-primary',
              ].join(' ')}
            >
              English
            </button>
            <button
              onClick={() => setLanguage('ur')}
              className={[
                'px-4 py-2 rounded-lg border text-sm font-medium transition-colors',
                language === 'ur'
                  ? 'bg-primary/10 border-primary text-primary'
                  : 'bg-bg-elevated border-border-subtle text-text-secondary hover:border-primary',
              ].join(' ')}
            >
              اردو
            </button>
          </div>
        </Card>

        <Card>
          <h3 className="text-text-primary font-semibold text-sm mb-3 flex items-center gap-2">
            {theme === 'dark'
              ? <Moon size={14} className="text-primary" />
              : <Sun size={14} className="text-primary" />}
            {t['settings.appearance']}
          </h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-primary text-sm">{t['settings.dark_mode']}</p>
              <p className="text-text-muted text-xs">
                {theme === 'dark' ? t['settings.dark_mode_desc'] : t['settings.light_mode_desc']}
              </p>
            </div>
            <button
              onClick={toggleTheme}
              className={[
                'w-10 h-5 rounded-full flex items-center px-0.5 transition-colors',
                theme === 'dark' ? 'bg-primary justify-end' : 'bg-border-subtle justify-start',
              ].join(' ')}
            >
              <div className="w-4 h-4 rounded-full bg-white" />
            </button>
          </div>
        </Card>

        <Card>
          <h3 className="text-text-primary font-semibold text-sm mb-3 flex items-center gap-2">
            <Watch size={14} className="text-primary" /> {t['wearables.title']}
          </h3>
          <p className="text-text-secondary text-xs mb-3">{t['wearables.subtitle']}</p>
          <button
            onClick={() => navigate('/wearables')}
            className="flex items-center gap-2 w-full bg-bg-elevated rounded-lg p-3 hover:border-primary border border-border-subtle transition-colors"
          >
            <Watch size={16} className="text-primary shrink-0" />
            <div className="flex-1 text-start">
              <p className="text-text-primary text-xs font-medium">{t['wearables.connect_demo']}</p>
              <p className="text-text-muted text-[10px]">Fitbit Charge 6 · Demo Provider</p>
            </div>
            <ChevronRight size={14} className="text-text-muted" />
          </button>
        </Card>

        <Card>
          <h3 className="text-text-primary font-semibold text-sm mb-3">{t['settings.ai_provider']}</h3>
          <div className="bg-bg-elevated rounded-lg p-3">
            <p className="text-text-secondary text-xs mb-1">{t['settings.current_provider']}</p>
            <p className="text-text-primary text-sm font-medium">Qwen (Alibaba Cloud)</p>
            <p className="text-text-muted text-xs mt-1">{t['settings.provider_config']}</p>
          </div>
        </Card>

        <Card padding="sm">
          <p className="text-text-muted text-xs text-center">
            {t['settings.version']}
          </p>
        </Card>
      </div>
    </PageWrapper>
  )
}
