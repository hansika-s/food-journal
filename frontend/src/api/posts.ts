import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { client, getCsrfToken } from './client'
import type { components } from './schema'

export type Post = components['schemas']['PostResponse']
export type PostInput = components['schemas']['PostCreate']
export type PostChanges = components['schemas']['PostUpdate']

export const postsKey = ['posts'] as const

// The list of the user's posts, newest first.
export function usePosts() {
  return useQuery({
    queryKey: postsKey,
    queryFn: async () => {
      const { data, response } = await client.GET('/api/posts')
      if (!data) throw new Error(`Could not load posts (${response.status})`)
      return data
    },
  })
}

// Every change to a post refreshes the list, so the screen shows the new data.
function useRefreshPosts() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: postsKey })
}

export function useCreatePost() {
  const refresh = useRefreshPosts()
  return useMutation({
    mutationFn: async (post: PostInput) => {
      const { data, response } = await client.POST('/api/posts', { body: post })
      if (!data) throw new Error(`Could not save post (${response.status})`)
      return data
    },
    onSuccess: refresh,
  })
}

export function useUpdatePost() {
  const refresh = useRefreshPosts()
  return useMutation({
    mutationFn: async ({ id, changes }: { id: string; changes: PostChanges }) => {
      const { data, response } = await client.PATCH('/api/posts/{post_id}', {
        params: { path: { post_id: id } },
        body: changes,
      })
      if (!data) throw new Error(`Could not save post (${response.status})`)
      return data
    },
    onSuccess: refresh,
  })
}

export function useDeletePost() {
  const refresh = useRefreshPosts()
  return useMutation({
    mutationFn: async (id: string) => {
      const { response } = await client.DELETE('/api/posts/{post_id}', {
        params: { path: { post_id: id } },
      })
      if (!response.ok) throw new Error(`Could not delete post (${response.status})`)
    },
    onSuccess: refresh,
  })
}

// Photos are sent with fetch, not the typed client, because the generated type for a file is just a string.
// The CSRF header is added here by hand.
export async function uploadPhoto(postId: string, file: File): Promise<void> {
  const body = new FormData()
  body.append('file', file)
  const response = await fetch(`/api/posts/${postId}/images`, {
    method: 'POST',
    headers: { 'X-CSRF-Token': getCsrfToken() ?? '' },
    body,
  })
  if (!response.ok) {
    // The server explains why in `detail`, such as "Only JPEG, PNG and WebP images are allowed".
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null
    const reason = typeof body?.detail === 'string' ? body.detail : `status ${response.status}`
    throw new Error(`${file.name}: ${reason}`)
  }
}

export function useDeletePhoto() {
  const refresh = useRefreshPosts()
  return useMutation({
    mutationFn: async ({ postId, imageId }: { postId: string; imageId: string }) => {
      const { response } = await client.DELETE('/api/posts/{post_id}/images/{image_id}', {
        params: { path: { post_id: postId, image_id: imageId } },
      })
      if (!response.ok) throw new Error(`Could not remove photo (${response.status})`)
    },
    onSuccess: refresh,
  })
}

// The URL of a photo. The browser sends the session cookie with it, so <img> works without extra setup.
export function photoUrl(postId: string, imageId: string): string {
  return `/api/posts/${postId}/images/${imageId}`
}
