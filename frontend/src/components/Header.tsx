import { useLocation, useNavigate } from 'react-router'
import { useSession } from '@/api/session'
import { AccountBar } from '@/components/AccountBar'
import { Button } from '@/components/ui/button'
import { Logo } from '@/components/Logo'

// The top bar on every page: the logo on the left; on the posts page, the New post button and the account button
// on the right.
export function Header() {
  const session = useSession()
  const location = useLocation()
  const navigate = useNavigate()
  const onPostsPage = location.pathname === '/'

  return (
    <header className="mb-6 flex items-start justify-between gap-4">
      <Logo />
      <div className="flex items-center gap-3">
        {session.data && onPostsPage && <Button onClick={() => navigate('/?new=1')}>New post</Button>}
        <AccountBar />
      </div>
    </header>
  )
}
