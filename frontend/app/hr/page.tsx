'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import type { JobListing } from '@/lib/types'

export default function HRDashboard() {
  const [listings, setListings] = useState<JobListing[]>([])
  const [loading, setLoading] = useState(true)
  const [userName, setUserName] = useState('')
  const router = useRouter()

  useEffect(() => {
    async function load() {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      setUserName(user?.user_metadata?.full_name || user?.email || '')

      const { data } = await supabase
        .from('job_listings')
        .select('*')
        .order('created_at', { ascending: false })

      setListings(data || [])
      setLoading(false)
    }
    load()
  }, [])

  const handleSignOut = async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <span className="brand">HR Assistant</span>
          <div className="header-right">
            <span className="user-badge hr-badge">HR</span>
            <span className="user-name">{userName}</span>
            <button className="btn-ghost-sm" onClick={handleSignOut}>Kijelentkezés</button>
          </div>
        </div>
      </header>

      <main className="site-main">
        <div className="page-hero">
          <div>
            <h1 className="page-title">Álláshirdetések</h1>
            <p className="page-sub">{listings.length} hirdetés összesen</p>
          </div>
          <Link href="/hr/jobs/new" className="btn-primary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Új hirdetés
          </Link>
        </div>

        {loading ? (
          <div className="loading-state">Betöltés...</div>
        ) : listings.length === 0 ? (
          <div className="empty-phase">
            <div className="empty-headline">Még nincs hirdetésed</div>
            <div className="empty-sub">Hozd létre az első álláshirdetésedet, és kezdj el CV-ket fogadni.</div>
            <Link href="/hr/jobs/new" className="btn-primary">Első hirdetés létrehozása</Link>
          </div>
        ) : (
          <div className="listings-grid">
            {listings.map((listing, i) => (
              <Link
                key={listing.id}
                href={`/hr/jobs/${listing.id}`}
                className="listing-card"
                style={{ animationDelay: `${i * 40}ms` }}
              >
                <div className="listing-card-top">
                  <span className={`status-dot ${listing.is_open ? 'open' : 'closed'}`} />
                  <span className="listing-status">{listing.is_open ? 'Nyitott' : 'Lezárt'}</span>
                </div>
                <div className="listing-title">{listing.title}</div>
                {listing.description && (
                  <div className="listing-desc">{listing.description}</div>
                )}
                <div className="listing-meta">
                  {new Date(listing.created_at).toLocaleDateString('hu-HU')}
                  {' · '}
                  {Object.values(listing.anonymization_config).filter(Boolean).length}/5 szűrő aktív
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </>
  )
}
