import { useState, type SubmitEvent } from 'react'
import { Navigate } from 'react-router'
import { useSession } from '@/api/session'
import { useUpdateProfile } from '@/api/profile'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function ProfilePage() {
  const session = useSession()
  const update = useUpdateProfile()
  const user = session.data?.user

  const [name, setName] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [saved, setSaved] = useState(false)
  const [loadedFor, setLoadedFor] = useState<string | null>(null)

  if (session.isPending) return <p>Loading…</p>
  if (!user) return <Navigate to="/login" replace />

  // Fill the form with the current details once, the first time the page shows this user.
  if (loadedFor !== user.id) {
    setLoadedFor(user.id)
    setName(user.name)
  }

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaved(false)
    update.mutate(
      {
        name,
        // An empty new password means "keep the current one". The current password is only needed to change it.
        new_password: newPassword || null,
        current_password: newPassword ? currentPassword : null,
      },
      {
        onSuccess: () => {
          setCurrentPassword('')
          setNewPassword('')
          setSaved(true)
        },
      },
    )
  }

  return (
    <Card className="mx-auto w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-lg">Your profile</CardTitle>
        <CardDescription>To change your password, enter your current password.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="profile-name">Name</Label>
            <Input id="profile-name" required value={name} onChange={(event) => setName(event.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="profile-new-password">New password (optional, at least 8 characters)</Label>
            <Input
              id="profile-new-password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="profile-current-password">Current password (needed to change the password)</Label>
            <Input
              id="profile-current-password"
              type="password"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
            />
          </div>
          {update.error && <p className="text-sm text-red-600">{update.error.message}</p>}
          {saved && !update.error && <p className="text-sm text-muted-foreground">Saved.</p>}
          <Button type="submit" disabled={update.isPending}>
            {update.isPending ? 'Saving…' : 'Save changes'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
