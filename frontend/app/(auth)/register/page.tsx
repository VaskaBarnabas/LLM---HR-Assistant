'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'

export default function RegisterPage() {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<'applicant' | 'hr'>('applicant')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const supabase = createClient()
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { role, full_name: fullName },
      },
    })

    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }

    router.push(role === 'hr' ? '/hr' : '/jobs')
    router.refresh()
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">HR Assistant</div>
        <h1 className="auth-title">Regisztráció</h1>

        <form onSubmit={handleRegister} className="auth-form">
          <div className="form-group">
            <label className="form-label">Teljes név</label>
            <input
              className="form-input"
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              placeholder="Kovács János"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="nev@ceg.hu"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Jelszó</label>
            <input
              className="form-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Minimum 6 karakter"
              required
              minLength={6}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Szerepkör</label>
            <div className="role-picker">
              <button
                type="button"
                className={`role-btn${role === 'applicant' ? ' active' : ''}`}
                onClick={() => setRole('applicant')}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
                Jelentkező
              </button>
              <button
                type="button"
                className={`role-btn${role === 'hr' ? ' active' : ''}`}
                onClick={() => setRole('hr')}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
                </svg>
                HR
              </button>
            </div>
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="btn-primary full-width" disabled={loading}>
            {loading ? 'Fiók létrehozása...' : 'Fiók létrehozása'}
          </button>
        </form>

        <div className="auth-footer">
          Már van fiókod?{' '}
          <Link href="/login" className="auth-link">Bejelentkezés</Link>
        </div>
      </div>
    </div>
  )
}
