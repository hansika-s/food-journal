import { useState } from 'react'
import { Navigate } from 'react-router'
import { useDeletePost, usePosts } from '@/api/posts'
import { useSession } from '@/api/session'
import { Button } from '@/components/ui/button'
import { PostCard } from '@/components/PostCard'
import { PostForm } from '@/components/PostForm'

// Which form is open: a new post ('new'), an existing post by its id, or none.
type Editing = 'new' | string | null

export function HomePage() {
  const session = useSession()
  const posts = usePosts()
  const deletePost = useDeletePost()
  const [editing, setEditing] = useState<Editing>(null)

  if (session.isPending) return <p>Loading…</p>
  if (!session.data) return <Navigate to="/login" replace />

  const closeForm = () => setEditing(null)

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <div className="flex justify-end">
        <Button onClick={() => setEditing('new')}>New post</Button>
      </div>

      {editing === 'new' && <PostForm onDone={closeForm} />}

      {posts.isPending && <p className="text-muted-foreground">Loading posts…</p>}
      {posts.error && <p className="text-sm text-red-600">{posts.error.message}</p>}
      {posts.data && posts.data.length === 0 && (
        <p className="text-muted-foreground">No posts yet. Add your first one.</p>
      )}

      <ul className="flex flex-col gap-6">
        {posts.data?.map((post) =>
          // Editing happens in place: the post's own card is replaced by the form.
          editing === post.id ? (
            <li key={post.id}>
              <PostForm post={post} onDone={closeForm} />
            </li>
          ) : (
            <PostCard
              key={post.id}
              post={post}
              onEdit={() => setEditing(post.id)}
              onDelete={() => deletePost.mutate(post.id)}
            />
          ),
        )}
      </ul>
    </div>
  )
}
