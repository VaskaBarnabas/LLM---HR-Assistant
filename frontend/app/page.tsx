'use client';

import { useState, useCallback, useRef } from 'react';

interface Candidate {
  id: string;
  name: string;
  email: string;
  phone: string;
  location: string;
  skills: string[];
  languages?: string[];
  fileName: string;
  analyzedAt: string;
  anonymizedHtml?: string;
}

export default function Home() {
  const [stagedFiles, setStagedFiles] = useState<File[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<Candidate | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [chatQuery, setChatQuery] = useState('');
  const [chatResults, setChatResults] = useState<{ id: string; distance: number; document: string }[]>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const hasCandidates = candidates.length > 0;
  const hasStaged = stagedFiles.length > 0;

  const filtered = candidates.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (Array.isArray(c.skills) && c.skills.some(s => s.toLowerCase().includes(searchQuery.toLowerCase()))) ||
    c.location.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const stageFiles = useCallback((files: File[]) => {
    const pdfs = files.filter(f => f.type === 'application/pdf');
    if (pdfs.length === 0) return;
    setStagedFiles(prev => {
      const existingNames = new Set(prev.map(f => f.name));
      return [...prev, ...pdfs.filter(f => !existingNames.has(f.name))];
    });
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); }, []);
  const handleDragLeave = useCallback(() => setIsDragging(false), []);
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    stageFiles(Array.from(e.dataTransfer.files));
  }, [stageFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    stageFiles(Array.from(e.target.files || []));
    e.target.value = '';
  }, [stageFiles]);

  const removeFile = (name: string) => setStagedFiles(prev => prev.filter(f => f.name !== name));

  const analyze = async () => {
    if (!hasStaged) return;
    setIsProcessing(true);
    try {
      const formData = new FormData();
      stagedFiles.forEach(f => formData.append('files', f));
      const res = await fetch('/api/analyze', { method: 'POST', body: formData });
      const data = await res.json();
      if (data.candidates) {
        setCandidates(prev => [...prev, ...data.candidates]);
        setStagedFiles([]);
      }
    } catch {
      // API not connected
    } finally {
      setIsProcessing(false);
    }
  };

  const sendChatQuery = async () => {
    if (!chatQuery.trim() || isChatLoading) return;
    setIsChatLoading(true);
    setChatResults([]);
    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: chatQuery.trim(), n_results: 3 }),
      });
      const data = await res.json();
      if (data.results) setChatResults(data.results);
    } catch {
      // API not connected
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleChatKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatQuery();
    }
  };

  // Phase 1: no files anywhere
  const phase = !hasStaged && !hasCandidates ? 1
    : hasStaged && !hasCandidates ? 2
    : 2.5; // hasStaged + hasCandidates, or just hasCandidates

  return (
    <>
      {/* Header */}
      <header className="site-header">
        <div className="header-inner">
          <span className="brand">HR Assistant</span>
          {hasCandidates && (
            <div className="header-search">
              <input
                type="text"
                placeholder="Search by name, skill or location…"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>
          )}
          <div className="header-right">
            {hasCandidates && <span className="candidate-count">{candidates.length} candidate{candidates.length !== 1 ? 's' : ''}</span>}
            {hasCandidates && (
              <button className="btn-upload" onClick={() => fileInputRef.current?.click()}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                Add more CVs
              </button>
            )}
            <input ref={fileInputRef} type="file" accept=".pdf" multiple onChange={handleFileInput} className="hidden" />
          </div>
        </div>
      </header>

      <main
        className="site-main"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >

        {/* ── PHASE 1: Empty state — upload prompt ── */}
        {phase === 1 && (
          <div className="empty-phase">
            <div className="empty-headline">Analyze CV files with AI</div>
            <div className="empty-sub">Upload one or more PDF CVs to extract skills, contact info and more.</div>
            <div
              className={`upload-zone${isDragging ? ' dragging' : ''}`}
              onClick={() => fileInputRef.current?.click()}
            >
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="upload-zone-icon">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="12" y1="18" x2="12" y2="12"/>
                <line x1="9" y1="15" x2="15" y2="15"/>
              </svg>
              <p className="upload-zone-label">{isDragging ? 'Drop your CVs here' : 'Drop CV files here'}</p>
              <p className="upload-zone-sub">or <span className="upload-zone-link">click to browse</span> · PDF · multiple files</p>
            </div>
          </div>
        )}

        {/* ── PHASE 2: Files staged — review & analyze ── */}
        {hasStaged && (
          <div className="staged-section">
            <div className="staged-header">
              <div>
                <div className="section-title">Ready to analyze</div>
                <div className="section-sub">{stagedFiles.length} file{stagedFiles.length !== 1 ? 's' : ''} selected · click Analyze to continue</div>
              </div>
              <button className="btn-ghost-sm" onClick={() => fileInputRef.current?.click()}>
                + Add more
              </button>
            </div>
            <div className="staged-grid">
              {stagedFiles.map(file => (
                <div key={file.name} className="staged-card">
                  <div className="staged-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                  </div>
                  <div className="staged-name">{file.name}</div>
                  <div className="staged-size">{(file.size / 1024).toFixed(0)} KB</div>
                  <button className="staged-remove" onClick={() => removeFile(file.name)} aria-label="Remove">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </div>
              ))}
            </div>

            <div className="analyze-bar">
              <button className="btn-analyze" onClick={analyze} disabled={isProcessing}>
                {isProcessing ? (
                  <><div className="processing-spinner small" />Analyzing…</>
                ) : (
                  <>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                    Analyze {stagedFiles.length} CV{stagedFiles.length !== 1 ? 's' : ''}
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ── PHASE 3: Candidates + chat ── */}
        {hasCandidates && (
          <>
            <div className="section-header">
              <span className="section-title">Candidates</span>
              <span className="section-count">{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
            </div>
            <div className="bento-grid">
              {filtered.map((c, i) => (
                <CandidateCard
                  key={c.id}
                  candidate={c}
                  index={i}
                  isSelected={selected?.id === c.id}
                  onClick={() => setSelected(prev => prev?.id === c.id ? null : c)}
                />
              ))}
              {filtered.length === 0 && (
                <div className="empty-state">No candidates match your search.</div>
              )}
            </div>

            {/* Chat input */}
            <div className="chat-section">
              <div className="chat-section-label">Ask a question about these candidates</div>
              <div className={`chat-box${isDragging ? ' dragging' : ''}`}>
                <textarea
                  className="chat-textarea"
                  placeholder="e.g. Who has the most React experience? Who speaks German?"
                  value={chatQuery}
                  onChange={e => setChatQuery(e.target.value)}
                  onKeyDown={handleChatKeyDown}
                  rows={3}
                />
                <button
                  className="chat-send-btn"
                  onClick={sendChatQuery}
                  disabled={isChatLoading || !chatQuery.trim()}
                  aria-label="Send"
                >
                  {isChatLoading ? (
                    <div className="processing-spinner small" />
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                    </svg>
                  )}
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

      {/* Detail side sheet */}
      {selected && (
        <DetailSheet candidate={selected} onClose={() => setSelected(null)} />
      )}
    </>
  );
}

function DetailSheet({ candidate, onClose }: { candidate: Candidate; onClose: () => void }) {
  const [cvOpen, setCvOpen] = useState(false);

  return (
    <>
      <div className="detail-backdrop" onClick={onClose} />
      <aside className="detail-sheet">
        <div className="sheet-header">
          <span className="sheet-title">Candidate Profile</span>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>
        <div className="sheet-name">{candidate.name}</div>

        <div className="sheet-section">
          <div className="sheet-section-label">Contact</div>
          <div className="detail-row"><div className="detail-key">Email</div><div className="detail-val">{candidate.email}</div></div>
          <div className="detail-row"><div className="detail-key">Phone</div><div className="detail-val">{candidate.phone}</div></div>
          <div className="detail-row"><div className="detail-key">Location</div><div className="detail-val">{candidate.location}</div></div>
        </div>

        <div className="sheet-section">
          <div className="sheet-section-label">Skills</div>
          <div className="skills-grid">
            {(Array.isArray(candidate.skills) ? candidate.skills : []).map(s => <span key={s} className="skill-tag">{s}</span>)}
          </div>
        </div>

        {candidate.languages && candidate.languages.length > 0 && (
          <div className="sheet-section">
            <div className="sheet-section-label">Languages</div>
            <div className="skills-grid">
              {candidate.languages.map(l => <span key={l} className="skill-tag lang-tag">{l}</span>)}
            </div>
          </div>
        )}

        {candidate.anonymizedHtml && (
          <div className="sheet-section">
            <button
              className="cv-toggle"
              onClick={() => setCvOpen(o => !o)}
              aria-expanded={cvOpen}
            >
              <svg
                width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2.5"
                style={{ transform: cvOpen ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
              Anonymized CV
            </button>
            {cvOpen && (
              <div
                className="cv-html-body"
                // Safe: HTML is generated server-side by anonymized_text_to_html()
                // which HTML-escapes all LLM output before wrapping in structural tags.
                // No user-supplied raw HTML ever reaches this field.
                dangerouslySetInnerHTML={{ __html: candidate.anonymizedHtml }}
              />
            )}
          </div>
        )}
      </aside>
    </>
  );
}

function CandidateCard({ candidate, index, isSelected, onClick }: {
  candidate: Candidate; index: number; isSelected: boolean; onClick: () => void;
}) {
  return (
    <div
      className={`candidate-card${isSelected ? ' selected' : ''}`}
      onClick={onClick}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="card-name">{candidate.name}</div>
      <div className="card-meta">
        <span>{candidate.location}</span>
        <span className="dot">·</span>
        <span>{Array.isArray(candidate.skills) ? candidate.skills.length : 0} skills</span>
      </div>
      <div className="card-skills">
        {(Array.isArray(candidate.skills) ? candidate.skills : []).slice(0, 3).map(s => (
          <span key={s} className="skill-pill">{s}</span>
        ))}
        {Array.isArray(candidate.skills) && candidate.skills.length > 3 && (
          <span className="skill-pill more">+{candidate.skills.length - 3}</span>
        )}
      </div>
    </div>
  );
}
