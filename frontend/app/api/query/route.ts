import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const body = await request.json();

  if (!body.query || typeof body.query !== 'string') {
    return NextResponse.json({ error: 'query is required' }, { status: 400 });
  }

  const res = await fetch(`${BACKEND_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: body.query, n_results: body.n_results ?? 3 }),
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
