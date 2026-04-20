'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    async function redirect() {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        router.replace('/login')
      } else {
        const role = user.user_metadata?.role
        router.replace(role === 'hr' ? '/hr' : '/jobs')
      }
    }
    redirect()
  }, [router])

  return (
    <div className="loading-screen">
      <div className="loading-spinner" />
    </div>
  )
}
