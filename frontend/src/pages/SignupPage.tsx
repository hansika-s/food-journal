import { useState, type SubmitEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router'
import { useSession, useSignup } from '@/api/session'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function SignupPage() {
  const session = useSession()
  const signup = useSignup()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  // Already logged in: go to the home page.
  if (session.data) return <Navigate to="/" replace />

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    signup.mutate({ name, email, password }, {
      onSuccess: () => navigate('/login', { replace: true }),
    })
  }

  return (
    <div className="flex justify-center">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardDescription>Create an account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" autoComplete="name" required value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" autoComplete="new-password" required minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            {signup.error && <p className="text-sm text-red-600">{signup.error.message}</p>}
            <Button type="submit" disabled={signup.isPending}>
              {signup.isPending ? 'Creating account…' : 'Sign up'}
            </Button>
            <p className="text-sm">
              Already have an account? <Link to="/login" className="underline">Log in</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
