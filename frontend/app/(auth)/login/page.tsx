'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const supabase = createClient()
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })

    if (error) {
      setError('Hibás email vagy jelszó.')
      setLoading(false)
      return
    }

    const role = data.user?.user_metadata?.role
    router.push(role === 'hr' ? '/hr' : '/jobs')
    router.refresh()
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">HR Assistant</div>
        <h1 className="auth-title">Bejelentkezés</h1>

        <form onSubmit={handleLogin} className="auth-form">
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
              placeholder="••••••••"
              required
            />
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="btn-primary full-width" disabled={loading}>
            {loading ? 'Bejelentkezés...' : 'Bejelentkezés'}
          </button>
        </form>

        <div className="auth-footer">
          Még nincs fiókod?{' '}
          <Link href="/register" className="auth-link">Regisztráció</Link>
        </div>
      </div>
    </div>
  )
}
