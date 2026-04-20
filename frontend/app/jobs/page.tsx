'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import type { JobListing } from '@/lib/types'

export default function JobsPage() {
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
        .eq('is_open', true)
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
            <span className="user-badge applicant-badge">Jelentkező</span>
            <span className="user-name">{userName}</span>
            <button className="btn-ghost-sm" onClick={handleSignOut}>Kijelentkezés</button>
          </div>
        </div>
      </header>

      <main className="site-main">
        <div className="page-hero">
          <div>
            <h1 className="page-title">Nyitott állások</h1>
            <p className="page-sub">{listings.length} nyitott hirdetés</p>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">Betöltés...</div>
        ) : listings.length === 0 ? (
          <div className="empty-phase">
            <div className="empty-headline">Jelenleg nincs nyitott hirdetés</div>
            <div className="empty-sub">Nézz vissza később!</div>
          </div>
        ) : (
          <div className="listings-grid">
            {listings.map((listing, i) => (
              <div key={listing.id} className="listing-card" style={{ animationDelay: `${i * 40}ms` }}>
                <div className="listing-card-top">
                  <span className="status-dot open" />
                  <span className="listing-status">Nyitott</span>
                </div>
                <div className="listing-title">{listing.title}</div>
                {listing.description && (
                  <div className="listing-desc">{listing.description}</div>
                )}
                <div className="listing-footer">
                  <span className="listing-meta">
                    {new Date(listing.created_at).toLocaleDateString('hu-HU')}
                  </span>
                  <Link href={`/jobs/${listing.id}/apply`} className="btn-primary small">
                    Jelentkezés
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </>
  )
}
