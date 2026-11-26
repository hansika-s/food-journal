import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { components } from './schema'
import { client } from './client'
import { sessionKey } from './session'

export type ProfileChanges = components['schemas']['ProfileUpdate']

// Saves changes to the account. Changing the password needs the current password.
export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (changes: ProfileChanges) => {
      const { data, response } = await client.PATCH('/api/users/me', { body: changes })
      if (!data) {
        throw new Error(
          response.status === 403
            ? 'Your current password is wrong'
            : `Could not save (${response.status})`,
        )
      }
      return data
    },
    // The header shows the name, so refresh the session.
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sessionKey }),
  })
}
