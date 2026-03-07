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
}

export default function Home() {
  const [stagedFiles, setStagedFiles] = useState<File[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<Candidate | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

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
      const newFiles = pdfs.filter(f => !existingNames.has(f.name));
      return [...prev, ...newFiles];
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

  const removeFile = (name: string) => {
    setStagedFiles(prev => prev.filter(f => f.name !== name));
  };

  const analyze = async () => {
    if (stagedFiles.length === 0) return;
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

  const hasCandidates = candidates.length > 0;

  return (
    <>
      {/* Header */}
      <header className="site-header">
        <div className="header-inner">
          <span className="brand">HR Analysis</span>
          {hasCandidates && (
            <div className="header-search">
              <input
                type="text"
                placeholder="Search candidates or skills..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>
          )}
          <div className="header-right">
            {hasCandidates && <span className="candidate-count">{candidates.length} candidates</span>}
            <button className="btn-upload" onClick={() => fileInputRef.current?.click()}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              Upload CVs
            </button>
            <input ref={fileInputRef} type="file" accept=".pdf" multiple onChange={handleFileInput} className="hidden" />
          </div>
        </div>
      </header>

      {/* Main */}
      <main
        className="site-main"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Drop zone — always visible */}
        <div
          className={`upload-zone${isDragging ? ' dragging' : ''}`}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="upload-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="12" y1="18" x2="12" y2="12"/>
              <line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
          </div>
          <p className="upload-label">Drag & drop CV files here</p>
          <p className="upload-sublabel">PDF format · multiple files supported</p>
        </div>

        {/* Staged files grid */}
        {stagedFiles.length > 0 && (
          <div className="staged-section">
            <div className="staged-header">
              <span className="section-title">
                Uploaded CVs
                <span className="section-count" style={{ marginLeft: '0.5rem' }}>{stagedFiles.length} file{stagedFiles.length !== 1 ? 's' : ''}</span>
              </span>
            </div>
            <div className="staged-grid">
              {stagedFiles.map(file => (
                <div key={file.name} className="staged-card">
                  <div className="staged-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                  </div>
                  <div className="staged-name">{file.name}</div>
                  <div className="staged-size">{(file.size / 1024).toFixed(0)} KB</div>
                  <button
                    className="staged-remove"
                    onClick={() => removeFile(file.name)}
                    aria-label="Remove file"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analyze button — always visible, disabled until files are staged */}
        <div className="analyze-bar">
          <button
            className="btn-analyze"
            onClick={analyze}
            disabled={stagedFiles.length === 0 || isProcessing}
          >
            {isProcessing ? (
              <>
                <div className="processing-spinner small" />
                Analyzing…
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Analyze CVs
              </>
            )}
          </button>
        </div>

        {/* Candidates bento grid */}
        {hasCandidates && (
          <>
            <div className="section-header">
              <span className="section-title">Candidates</span>
              <span className="section-count">{filtered.length} results</span>
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
          </>
        )}
      </main>

      {/* Detail side sheet */}
      {selected && (
        <>
          <div className="detail-backdrop" onClick={() => setSelected(null)} />
          <aside className="detail-sheet">
            <div className="sheet-header">
              <span className="sheet-title">Candidate Profile</span>
              <button className="btn-close" onClick={() => setSelected(null)}>✕</button>
            </div>
            <div className="sheet-name">{selected.name}</div>

            <div className="sheet-section">
              <div className="sheet-section-label">Contact</div>
              <div className="detail-row">
                <div className="detail-key">Email</div>
                <div className="detail-val">{selected.email}</div>
              </div>
              <div className="detail-row">
                <div className="detail-key">Phone</div>
                <div className="detail-val">{selected.phone}</div>
              </div>
              <div className="detail-row">
                <div className="detail-key">Location</div>
                <div className="detail-val">{selected.location}</div>
              </div>
            </div>

            <div className="sheet-section">
              <div className="sheet-section-label">Skills</div>
              <div className="skills-grid">
                {(Array.isArray(selected.skills) ? selected.skills : []).map(s => <span key={s} className="skill-tag">{s}</span>)}
              </div>
            </div>

            {selected.languages && selected.languages.length > 0 && (
              <div className="sheet-section">
                <div className="sheet-section-label">Languages</div>
                <div className="skills-grid">
                  {selected.languages.map(l => <span key={l} className="skill-tag lang-tag">{l}</span>)}
                </div>
              </div>
            )}
          </aside>
        </>
      )}
    </>
  );
}

function CandidateCard({ candidate, index, isSelected, onClick }: {
  candidate: Candidate;
  index: number;
  isSelected: boolean;
  onClick: () => void;
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
