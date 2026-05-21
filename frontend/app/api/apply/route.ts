import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000'

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const formData = await request.formData()
  const jobListingId = formData.get('job_listing_id') as string
  const file = formData.get('file') as File | null

  if (!file || !jobListingId) {
    return NextResponse.json({ error: 'Hiányzó adat' }, { status: 400 })
  }

  // Ensure profile exists for this user
  await supabase.from('profiles').upsert({
    id: user.id,
    role: user.user_metadata?.role || 'applicant',
    full_name: user.user_metadata?.full_name || '',
  }, { onConflict: 'id' })

  // Fetch the job listing's anonymization config
  const { data: listing } = await supabase
    .from('job_listings')
    .select('anonymization_config, is_open')
    .eq('id', jobListingId)
    .single()

  if (!listing || !listing.is_open) {
    return NextResponse.json({ error: 'A hirdetés nem található vagy lezárt' }, { status: 404 })
  }

  // Forward to Python backend with anonymization filters
  const backendForm = new FormData()
  backendForm.append('files', file, file.name)
  backendForm.append('filters', JSON.stringify(listing.anonymization_config))

  const backendRes = await fetch(`${BACKEND_URL}/analyze`, {
    method: 'POST',
    body: backendForm,
  })

  if (!backendRes.ok) {
    const body = await backendRes.json().catch(() => null)
    const errorMsg = body?.error ?? 'Hiba történt az anonimizálás során.'
    const status = backendRes.status === 422 ? 422 : 500
    return NextResponse.json({ error: errorMsg }, { status })
  }

  const result = await backendRes.json()
  const candidate = result.candidates?.[0]

  if (!candidate) {
    return NextResponse.json({ error: 'Nem sikerült feldolgozni a CV-t' }, { status: 500 })
  }

  // Store application in Supabase
  const { data: inserted, error } = await supabase.from('applications').insert({
    job_listing_id: jobListingId,
    applicant_id: user.id,
    analyzed_data: {
      name: candidate.name,
      email: candidate.email,
      phone: candidate.phone,
      location: candidate.location,
      skills: candidate.skills,
      languages: candidate.languages,
    },
    anonymized_html: candidate.anonymizedHtml ?? null,
  }).select('id').single()

  if (error) {
    if (error.code === '23505') {
      return NextResponse.json({ error: 'Már jelentkeztél erre az állásra' }, { status: 409 })
    }
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  // Store CV text in ChromaDB with the application_id so ranking can find it
  if (inserted?.id && candidate.cvText) {
    await fetch(`${BACKEND_URL}/store-cv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ application_id: inserted.id, cv_text: candidate.cvText }),
    }).catch(() => { /* non-critical */ })
  }

  return NextResponse.json({ success: true })
}
