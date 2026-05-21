'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import type { JobListing } from '@/lib/types'
import { Progress } from '@/components/ui/progress'

type Status = 'idle' | 'uploading' | 'success' | 'error' | 'already_applied'

const STEPS = [
  { label: 'Önéletrajz feltöltése…',                       until: 12 },
  { label: 'Nevek anonimizálása…',                          until: 30 },
  { label: 'Nemi munkakörmegnevezések semlegesítése…',      until: 48 },
  { label: 'Nemi névmások cseréje…',                        until: 63 },
  { label: 'Családi állapot eltávolítása…',                 until: 77 },
  { label: 'Nemi életesemények semlegesítése…',             until: 89 },
  { label: 'Eredmény ellenőrzése és mentés…',               until: 100 },
]

function getStepLabel(progress: number): string {
  return (STEPS.find(s => progress < s.until) ?? STEPS[STEPS.length - 1]).label
}

export default function ApplyPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()

  const [listing, setListing] = useState<JobListing | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [progress, setProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (status !== 'uploading') return
    setProgress(0)
    const id = setInterval(() => {
      setProgress(prev => {
        const increment = Math.max(0.4, (93 - prev) / 18)
        return Math.min(93, prev + increment)
      })
    }, 700)
    return () => clearInterval(id)
  }, [status])

  useEffect(() => {
    async function load() {
      const supabase = createClient()
      const { data } = await supabase
        .from('job_listings').select('*').eq('id', id).eq('is_open', true).single()
      if (!data) { router.push('/jobs'); return }
      setListing(data)
    }
    load()
  }, [id, router])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = Array.from(e.dataTransfer.files).find(f => f.type === 'application/pdf')
    if (dropped) setFile(dropped)
  }, [])

  const handleSubmit = async () => {
    if (!file || status === 'uploading') return
    setStatus('uploading')
    setErrorMsg('')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('job_listing_id', id)

    try {
      const res = await fetch('/api/apply', { method: 'POST', body: formData })
      const data = await res.json()

      setProgress(100)
      await new Promise(r => setTimeout(r, 400))

      if (res.status === 409) {
        setStatus('already_applied')
      } else if (!res.ok) {
        setErrorMsg(data.error || 'Hiba történt a feltöltés során.')
        setStatus('error')
      } else {
        setStatus('success')
      }
    } catch {
      setErrorMsg('Nem sikerült csatlakozni a szerverhez.')
      setStatus('error')
    }
  }

  if (!listing) return <div className="loading-screen"><div className="loading-spinner" /></div>

  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <Link href="/jobs" className="brand">HR Assistant</Link>
          <div className="header-right">
            <span className="breadcrumb">Állások / Jelentkezés</span>
          </div>
        </div>
      </header>

      <main className="site-main">
        <div className="form-page">
          <Link href="/jobs" className="back-link" style={{ marginBottom: '16px', display: 'inline-flex' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            Vissza az állásokhoz
          </Link>

          <h1 className="page-title">{listing.title}</h1>
          {listing.description && <p className="page-sub" style={{ marginBottom: '32px' }}>{listing.description}</p>}

          {status === 'success' ? (
            <div className="success-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/>
              </svg>
              <h2>Jelentkezés elküldve!</h2>
              <p>Önéletrajzod sikeresen feldolgoztuk. A HR csapat értesít, ha továbblépnek veled.</p>
              <Link href="/jobs" className="btn-primary" style={{ marginTop: '16px' }}>Vissza az állásokhoz</Link>
            </div>
          ) : status === 'already_applied' ? (
            <div className="success-state">
              <h2>Már jelentkeztél erre az állásra</h2>
              <p>Korábban már beküldted önéletrajzod erre a pozícióra.</p>
              <Link href="/jobs" className="btn-primary" style={{ marginTop: '16px' }}>Vissza az állásokhoz</Link>
            </div>
          ) : (
            <div className="apply-form">
              <div className="form-section">
                <h2 className="form-section-title">Önéletrajz feltöltése</h2>
                <p className="form-section-sub">
                  Az önéletrajzod automatikus anonimizáláson esik át az elfogultság csökkentése érdekében,
                  mielőtt a HR csapat megtekintené.
                </p>

                {file ? (
                  <div className="staged-card" style={{ maxWidth: '400px' }}>
                    <div className="staged-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                      </svg>
                    </div>
                    <div className="staged-name">{file.name}</div>
                    <div className="staged-size">{(file.size / 1024).toFixed(0)} KB</div>
                    <button className="staged-remove" onClick={() => setFile(null)}>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>
                ) : (
                  <div
                    className={`upload-zone${isDragging ? ' dragging' : ''}`}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={handleDrop}
                  >
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="upload-zone-icon">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                      <line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>
                    </svg>
                    <p className="upload-zone-label">{isDragging ? 'Engedd el itt' : 'Húzd ide a CV-t'}</p>
                    <p className="upload-zone-sub">vagy <span className="upload-zone-link">tallózz</span> · csak PDF</p>
                  </div>
                )}
                <input ref={fileInputRef} type="file" accept=".pdf" className="hidden"
                  onChange={e => { const f = e.target.files?.[0]; if (f) setFile(f); e.target.value = '' }} />
              </div>

              {status === 'error' && <div className="auth-error">{errorMsg}</div>}

              {status === 'uploading' && (
                <div className="upload-progress">
                  <div
                    className="upload-progress-bar"
                    style={{ '--primary': '#2563EB' } as React.CSSProperties}
                  >
                    <Progress value={progress} />
                  </div>
                  <div className="upload-progress-label">{getStepLabel(progress)}</div>
                </div>
              )}

              <div className="form-actions">
                <Link href="/jobs" className="btn-ghost">Mégse</Link>
                <button className="btn-analyze" onClick={handleSubmit} disabled={!file || status === 'uploading'}>
                  {status === 'uploading' ? (
                    <><div className="processing-spinner small" />Feldolgozás...</>
                  ) : (
                    <>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                      </svg>
                      Jelentkezés beküldése
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  )
}
