import { useLogout, useSession } from '@/api/session'
import { Button } from '@/components/ui/button'

// Shows who is logged in, with a log out button. Shows nothing when nobody is logged in.
export function AccountBar() {
  const session = useSession()
  const logout = useLogout()

  if (!session.data) return null

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-muted-foreground">Signed in as {session.data.user.name}</span>
      <Button variant="outline" size="sm" onClick={() => logout.mutate()} disabled={logout.isPending}>
        Log out
      </Button>
    </div>
  )
}
