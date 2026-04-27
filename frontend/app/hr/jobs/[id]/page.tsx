'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import {
  type JobListing, type Application, type Candidate, type AnonymizationConfig,
  ANON_FILTER_LABELS, applicationToCandidate,
} from '@/lib/types'

export default function HRJobDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()

  const [listing, setListing] = useState<JobListing | null>(null)
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [selected, setSelected] = useState<Candidate | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [chatQuery, setChatQuery] = useState('')
  const [chatResults, setChatResults] = useState<{ id: string; distance: number; document: string }[]>([])
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [editingConfig, setEditingConfig] = useState(false)
  const [config, setConfig] = useState<AnonymizationConfig | null>(null)
  const [rankings, setRankings] = useState<{ id: string; rank: number; name: string; skills: string[]; location: string; explanation: string }[] | null>(null)
  const [isRanking, setIsRanking] = useState(false)

  const load = useCallback(async () => {
    const supabase = createClient()
    const { data: listingData } = await supabase
      .from('job_listings').select('*').eq('id', id).single()

    if (!listingData) { router.push('/hr'); return }
    setListing(listingData)
    setConfig(listingData.anonymization_config)

    const { data: apps } = await supabase
      .from('applications').select('*').eq('job_listing_id', id)
      .order('submitted_at', { ascending: false })

    setCandidates((apps as Application[] || []).map(applicationToCandidate))
    setLoading(false)
  }, [id, router])

  useEffect(() => { load() }, [load])

  const saveConfig = async () => {
    if (!config) return
    const supabase = createClient()
    await supabase.from('job_listings').update({ anonymization_config: config }).eq('id', id)
    setEditingConfig(false)
    setListing(prev => prev ? { ...prev, anonymization_config: config } : prev)
  }

  const toggleOpen = async () => {
    if (!listing) return
    const supabase = createClient()
    const newOpen = !listing.is_open
    await supabase.from('job_listings').update({ is_open: newOpen }).eq('id', id)
    setListing(prev => prev ? { ...prev, is_open: newOpen } : prev)
  }

  const sendChatQuery = async () => {
    if (!chatQuery.trim() || isChatLoading) return
    setIsChatLoading(true)
    setChatResults([])
    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: chatQuery.trim(), n_results: 3 }),
      })
      const data = await res.json()
      if (data.results) setChatResults(data.results)
    } catch { /* ignore */ } finally { setIsChatLoading(false) }
  }

  const fetchRankings = async () => {
    if (!listing || candidates.length === 0 || isRanking) return
    setIsRanking(true)
    setRankings(null)
    try {
      const res = await fetch('/api/rank', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_title: listing.title,
          job_description: listing.description || '',
          candidates: candidates.map(c => ({
            id: c.id,
            name: c.name,
            skills: c.skills,
            languages: c.languages || [],
            location: c.location,
          })),
        }),
      })
      const data = await res.json()
      if (data.rankings) setRankings(data.rankings)
    } catch { /* ignore */ } finally { setIsRanking(false) }
  }

  const filtered = candidates.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.skills.some(s => s.toLowerCase().includes(searchQuery.toLowerCase())) ||
    c.location.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /></div>
  if (!listing) return null

  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <Link href="/hr" className="brand">HR Assistant</Link>
          {candidates.length > 0 && (
            <div className="header-search">
              <input type="text" placeholder="Keresés…" value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)} className="search-input" />
            </div>
          )}
          <div className="header-right">
            <span className="candidate-count">{candidates.length} jelentkező</span>
          </div>
        </div>
      </header>

      <main className="site-main">
        <div className="job-info-bar">
          <div className="job-info-left">
            <Link href="/hr" className="back-link">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="15 18 9 12 15 6"/>
              </svg>
              Hirdetések
            </Link>
            <h1 className="job-info-title">{listing.title}</h1>
          </div>
          <div className="job-info-right">
            <button className={`status-toggle ${listing.is_open ? 'open' : 'closed'}`} onClick={toggleOpen}>
              <span className="status-dot" />
              {listing.is_open ? 'Nyitott' : 'Lezárt'}
            </button>
          
          </div>
        </div>

        {editingConfig && config && (
          <div className="config-panel">
            <div className="config-panel-title">Anonimizációs szűrők</div>
            <div className="filter-list inline">
              {(Object.keys(config) as (keyof AnonymizationConfig)[]).map(key => (
                <div key={key} className="filter-row">
                  <span className="filter-label">{ANON_FILTER_LABELS[key]}</span>
                  <button type="button" className={`toggle-btn${config[key] ? ' on' : ''}`}
                    onClick={() => setConfig(prev => prev ? { ...prev, [key]: !prev[key] } : prev)}
                    role="switch" aria-checked={config[key]}>
                    <span className="toggle-knob" />
                  </button>
                </div>
              ))}
            </div>
            <div className="config-panel-actions">
              <button className="btn-ghost-sm" onClick={() => { setEditingConfig(false); setConfig(listing.anonymization_config) }}>Mégse</button>
              <button className="btn-primary small" onClick={saveConfig}>Mentés</button>
            </div>
          </div>
        )}

        {candidates.length === 0 ? (
          <div className="empty-phase">
            <div className="empty-headline">Még nincs jelentkező</div>
            <div className="empty-sub">Oszd meg a hirdetés linkjét a jelentkezők felé.</div>
          </div>
        ) : (
          <>
            <div className="section-header">
              <span className="section-title">Jelentkezők</span>
              <span className="section-count">{filtered.length} találat</span>
              <button className="btn-rank" onClick={fetchRankings} disabled={isRanking}>
                {isRanking ? <><div className="processing-spinner small" /> Rangsorolás...</> : 'Rangsorolás'}
              </button>
            </div>
            {rankings && (
              <div className="ranking-panel">
                <div className="ranking-title">Top 5 jelölt – {listing.title}</div>
                <div className="ranking-cards">
                  {rankings.map(r => (
                    <div key={r.id} className="ranking-card"
                      onClick={() => { const c = candidates.find(x => x.id === r.id); if (c) setSelected(c) }}>
                      <div className="ranking-badge">#{r.rank}</div>
                      <div className="ranking-card-body">
                        <div className="ranking-card-name">{r.name}</div>
                        {r.location && <div className="ranking-card-location">{r.location}</div>}
                        {r.explanation && <div className="ranking-card-explanation">{r.explanation}</div>}
                      </div>
                      <div className="ranking-card-skills">
                        {r.skills.slice(0, 4).map(s => <span key={s} className="skill-pill">{s}</span>)}
                        {r.skills.length > 4 && <span className="skill-pill more">+{r.skills.length - 4}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="bento-grid">
              {filtered.map((c, i) => (
                <CandidateCard key={c.id} candidate={c} index={i}
                  isSelected={selected?.id === c.id}
                  onClick={() => setSelected(prev => prev?.id === c.id ? null : c)} />
              ))}
              {filtered.length === 0 && <div className="empty-state">Nincs találat.</div>}
            </div>
            <div className="chat-section">
              <div className="chat-section-label">Kérdezz a jelentkezőkről</div>
              <div className="chat-box">
                <textarea className="chat-textarea" rows={3}
                  placeholder="pl. Ki rendelkezik a legtöbb React tapasztalattal?"
                  value={chatQuery} onChange={e => setChatQuery(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatQuery() } }} />
                <button className="chat-send-btn" onClick={sendChatQuery} disabled={isChatLoading || !chatQuery.trim()}>
                  {isChatLoading
                    ? <div className="processing-spinner small" />
                    : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>}
                </button>
              </div>
              {chatResults.length > 0 && (
                <div className="chat-results">
                  {chatResults.map((r, i) => (
                    <div key={r.id} className="chat-result-card">
                      <div className="chat-result-index">#{i + 1}</div>
                      <div className="chat-result-text">{r.document}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </main>

      {selected && <DetailSheet candidate={selected} onClose={() => setSelected(null)} />}
    </>
  )
}

function CandidateCard({ candidate, index, isSelected, onClick }: {
  candidate: Candidate; index: number; isSelected: boolean; onClick: () => void
}) {
  return (
    <div className={`candidate-card${isSelected ? ' selected' : ''}`} onClick={onClick}
      style={{ animationDelay: `${index * 50}ms` }}>
      <div className="card-name">{candidate.name}</div>
      <div className="card-meta">
        <span>{candidate.location}</span><span className="dot">·</span>
        <span>{candidate.skills.length} skill</span>
      </div>
      <div className="card-skills">
        {candidate.skills.slice(0, 3).map(s => <span key={s} className="skill-pill">{s}</span>)}
        {candidate.skills.length > 3 && <span className="skill-pill more">+{candidate.skills.length - 3}</span>}
      </div>
    </div>
  )
}

function DetailSheet({ candidate, onClose }: { candidate: Candidate; onClose: () => void }) {
  const [cvOpen, setCvOpen] = useState(false)

  return (
    <>
      <div className="detail-backdrop" onClick={onClose} />
      <aside className="detail-sheet">
        <div className="sheet-header">
          <span className="sheet-title">Jelentkező profilja</span>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>
        <div className="sheet-inner">
          <div className="sheet-name">{candidate.name}</div>
          <div className="sheet-body-grid">
            <div className="sheet-section">
              <div className="sheet-section-label">Kapcsolat</div>
              <div className="detail-row"><div className="detail-key">Email</div><div className="detail-val">{candidate.email}</div></div>
              <div className="detail-row"><div className="detail-key">Telefon</div><div className="detail-val">{candidate.phone}</div></div>
              <div className="detail-row"><div className="detail-key">Helyszín</div><div className="detail-val">{candidate.location}</div></div>
            </div>
            <div className="sheet-section">
              <div className="sheet-section-label">Skillек</div>
              <div className="skills-grid">{candidate.skills.map(s => <span key={s} className="skill-tag">{s}</span>)}</div>
            </div>
            {candidate.languages && candidate.languages.length > 0 && (
              <div className="sheet-section">
                <div className="sheet-section-label">Nyelvek</div>
                <div className="skills-grid">{candidate.languages.map(l => <span key={l} className="skill-tag lang-tag">{l}</span>)}</div>
              </div>
            )}
          </div>
          {candidate.anonymizedHtml && (
            <div className="sheet-section">
              <button className="cv-toggle" onClick={() => setCvOpen(o => !o)} aria-expanded={cvOpen}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
                  style={{ transform: cvOpen ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
                Anonimizált önéletrajz
              </button>
              {cvOpen && (
                <div className="cv-html-body" dangerouslySetInnerHTML={{ __html: candidate.anonymizedHtml }} />
              )}
            </div>
          )}
        </div>
      </aside>
    </>
  )
}
