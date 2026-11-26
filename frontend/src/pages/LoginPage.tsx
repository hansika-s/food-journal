import { useState, type SubmitEvent } from 'react'
import { Link, Navigate } from 'react-router'
import { useLogin, useSession } from '@/api/session'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function LoginPage() {
  const session = useSession()
  const login = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  // Already logged in: go to the home page.
  if (session.data) return <Navigate to="/" replace />

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    login.mutate({ email, password })
  }

  return (
    <div className="flex justify-center">
    <Card className="w-full max-w-sm rounded-3xl">
      <CardHeader>
        <CardDescription>Sign in to your food journal</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
          </div>
          {login.error && <p className="text-sm text-red-600">{login.error.message}</p>}
          <Button type="submit" disabled={login.isPending}>
            {login.isPending ? 'Logging in…' : 'Log in'}
          </Button>
          <p className="text-sm">
            No account? <Link to="/signup" className="underline">Sign up</Link>
          </p>
        </form>
      </CardContent>
    </Card>
    </div>
  )
}
