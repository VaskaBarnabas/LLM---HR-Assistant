'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { DEFAULT_ANON_CONFIG, ANON_FILTER_LABELS, type AnonymizationConfig } from '@/lib/types'

export default function NewJobPage() {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [config, setConfig] = useState<AnonymizationConfig>({ ...DEFAULT_ANON_CONFIG })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const toggle = (key: keyof AnonymizationConfig) => {
    setConfig(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    setLoading(true)
    setError('')

    const supabase = createClient()
    const { data: { user } } = await supabase.auth.getUser()

    // Ensure profile exists (trigger may not have run for users created before the trigger was added)
    await supabase.from('profiles').upsert({
      id: user!.id,
      role: user!.user_metadata?.role || 'hr',
      full_name: user!.user_metadata?.full_name || '',
    }, { onConflict: 'id' })

    const { data, error } = await supabase
      .from('job_listings')
      .insert({
        created_by: user!.id,
        title: title.trim(),
        description: description.trim() || null,
        is_open: true,
        anonymization_config: config,
      })
      .select('id')
      .single()

    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }

    router.push(`/hr/jobs/${data.id}`)
  }

  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <Link href="/hr" className="brand">HR Assistant</Link>
          <div className="header-right">
            <span className="breadcrumb">Álláshirdetések / Új</span>
          </div>
        </div>
      </header>

      <main className="site-main">
        <div className="form-page">
          <h1 className="page-title">Új álláshirdetés</h1>

          <form onSubmit={handleSubmit} className="job-form">
            <div className="form-section">
              <h2 className="form-section-title">Alapadatok</h2>

              <div className="form-group">
                <label className="form-label">Pozíció neve <span className="required">*</span></label>
                <input
                  className="form-input"
                  type="text"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder="pl. Senior Frontend Developer"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Leírás</label>
                <textarea
                  className="form-textarea"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="A pozícióról rövid leírás a jelentkezőknek..."
                  rows={4}
                />
              </div>
            </div>

            <div className="form-section">
              <h2 className="form-section-title">Anonimizációs szűrők</h2>
              <p className="form-section-sub">
                Válaszd ki, melyik szűrők fussanak le a beérkező CV-kre. A bekapcsolt szűrők eltávolítják
                a megfelelő információkat a CV-ből az elfogultság csökkentése érdekében.
              </p>

              <div className="filter-list">
                {(Object.keys(config) as (keyof AnonymizationConfig)[]).map(key => (
                  <div key={key} className="filter-row">
                    <div className="filter-info">
                      <span className="filter-label">{ANON_FILTER_LABELS[key]}</span>
                    </div>
                    <button
                      type="button"
                      className={`toggle-btn${config[key] ? ' on' : ''}`}
                      onClick={() => toggle(key)}
                      aria-checked={config[key]}
                      role="switch"
                    >
                      <span className="toggle-knob" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {error && <div className="auth-error">{error}</div>}

            <div className="form-actions">
              <Link href="/hr" className="btn-ghost">Mégse</Link>
              <button type="submit" className="btn-primary" disabled={loading || !title.trim()}>
                {loading ? 'Mentés...' : 'Hirdetés létrehozása'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </>
  )
}
