import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()
  const path = request.nextUrl.pathname
  const role = user?.user_metadata?.role as string | undefined

  // Root: redirect based on auth state
  if (path === '/') {
    if (!user) return NextResponse.redirect(new URL('/login', request.url))
    return NextResponse.redirect(new URL(role === 'hr' ? '/hr' : '/jobs', request.url))
  }

  // Auth pages: redirect already-logged-in users away
  if (path === '/login' || path === '/register') {
    if (user) {
      return NextResponse.redirect(new URL(role === 'hr' ? '/hr' : '/jobs', request.url))
    }
    return supabaseResponse
  }

  // All other protected routes: require login
  if (!user) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Role enforcement: applicants cannot access /hr
  if (path.startsWith('/hr') && role !== 'hr') {
    return NextResponse.redirect(new URL('/jobs', request.url))
  }

  return supabaseResponse
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'],
}
