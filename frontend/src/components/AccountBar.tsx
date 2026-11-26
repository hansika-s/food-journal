import { useNavigate } from 'react-router'
import { useLogout, useSession } from '@/api/session'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

// The account button: a circle with the first letter of the name. It opens a menu with the profile and log out.
// Shows nothing when nobody is logged in.
export function AccountBar() {
  const session = useSession()
  const logout = useLogout()
  const navigate = useNavigate()

  if (!session.data) return null

  const name = session.data.user.name
  const initial = name.trim().charAt(0).toUpperCase() || '?'

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label={`Account for ${name}`}
        className="flex size-9 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
      >
        {initial}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-40">
        <DropdownMenuGroup>
          <DropdownMenuLabel>{name}</DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => navigate('/profile')}>Profile</DropdownMenuItem>
        <DropdownMenuItem onClick={() => logout.mutate()}>Log out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
