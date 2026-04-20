import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const formData = await request.formData();
  const files = formData.getAll('files') as File[];
  const filters = formData.get('filters') as string | null;

  if (files.length === 0) {
    return NextResponse.json({ error: 'No files provided' }, { status: 400 });
  }

  const backendForm = new FormData();
  for (const file of files) {
    backendForm.append('files', file, file.name);
  }
  if (filters) {
    backendForm.append('filters', filters);
  }

  const res = await fetch(`${BACKEND_URL}/analyze`, {
    method: 'POST',
    body: backendForm,
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
