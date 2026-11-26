import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { client, setCsrfToken } from './client'

export const sessionKey = ['session'] as const

// Asks the server who is logged in. Returns null when nobody is.
export function useSession() {
  return useQuery({
    queryKey: sessionKey,
    queryFn: async () => {
      const { data, response } = await client.GET('/api/auth/session')
      if (response.status === 401) {
        setCsrfToken(null)
        return null
      }
      if (!data) throw new Error(`Could not load session (${response.status})`)
      setCsrfToken(data.csrf_token)
      return data
    },
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const { data, response } = await client.POST('/api/auth/login', { body: credentials })
      if (!data) {
        throw new Error(response.status === 401 ? 'Wrong email or password' : `Login failed (${response.status})`)
      }
      return data
    },
    onSuccess: (data) => {
      setCsrfToken(data.csrf_token)
      // The login response has no user details, so ask the server again. This fills the session data.
      void queryClient.invalidateQueries({ queryKey: sessionKey })
    },
  })
}

// Creates an account. Doesn't log in, so the user goes to the login page next.
export function useSignup() {
  return useMutation({
    mutationFn: async (details: { name: string; email: string; password: string }) => {
      const { data, response } = await client.POST('/api/auth/signup', { body: details })
      if (!data) {
        throw new Error(
          response.status === 409
            ? 'That email is already registered'
            : 'Check your details. The password needs at least 8 characters.',
        )
      }
      return data
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => client.POST('/api/auth/logout'),
    onSettled: () => {
      setCsrfToken(null)
      void queryClient.invalidateQueries({ queryKey: sessionKey })
    },
  })
}
