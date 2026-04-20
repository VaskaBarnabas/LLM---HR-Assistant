export type UserRole = 'hr' | 'applicant'

export interface AnonymizationConfig {
  names: boolean
  gendered_nouns: boolean
  pronouns: boolean
  family_status: boolean
  life_events: boolean
}

export const DEFAULT_ANON_CONFIG: AnonymizationConfig = {
  names: true,
  gendered_nouns: true,
  pronouns: true,
  family_status: true,
  life_events: true,
}

export const ANON_FILTER_LABELS: Record<keyof AnonymizationConfig, string> = {
  names: 'Nevek anonimizálása',
  gendered_nouns: 'Nemi munkakörmegnevezések semlegesítése',
  pronouns: 'Nemi névmások cseréje',
  family_status: 'Családi állapot eltávolítása',
  life_events: 'Nemi életesemények semlegesítése',
}

export interface JobListing {
  id: string
  created_by: string
  title: string
  description: string | null
  is_open: boolean
  anonymization_config: AnonymizationConfig
  created_at: string
}

export interface Application {
  id: string
  job_listing_id: string
  applicant_id: string
  status: 'pending' | 'reviewed'
  analyzed_data: {
    name?: string
    email?: string
    phone?: string
    location?: string
    skills?: string[]
    languages?: string[]
  } | null
  anonymized_html: string | null
  submitted_at: string
}

export interface Candidate {
  id: string
  name: string
  email: string
  phone: string
  location: string
  skills: string[]
  languages?: string[]
  anonymizedHtml?: string
  submittedAt: string
}

export function applicationToCandidate(app: Application): Candidate {
  const d = app.analyzed_data || {}
  return {
    id: app.id,
    name: d.name || 'Ismeretlen',
    email: d.email || '',
    phone: d.phone || '',
    location: d.location || '',
    skills: d.skills || [],
    languages: d.languages,
    anonymizedHtml: app.anonymized_html || undefined,
    submittedAt: app.submitted_at,
  }
}
