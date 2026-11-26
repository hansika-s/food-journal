import { useState } from 'react'
import { Navigate, useSearchParams } from 'react-router'
import { useDeletePost, usePosts, type PostFilters } from '@/api/posts'
import { useSession } from '@/api/session'
import { Button } from '@/components/ui/button'
import { PostCard } from '@/components/PostCard'
import { PostFilterBar } from '@/components/PostFilterBar'
import { PostForm } from '@/components/PostForm'
import { useLoadMoreOnScroll } from '@/lib/useLoadMoreOnScroll'

// The form open for an existing post, by its id. A new post is opened with ?new=1 in the address.
type Editing = string | null

export function HomePage() {
  const session = useSession()
  const [filters, setFilters] = useState<PostFilters>({})
  const posts = usePosts(filters)
  // Loads the next page as the bottom of the list comes into view. Stops while a page loads or after a failure.
  const loadMoreRef = useLoadMoreOnScroll(
    Boolean(posts.hasNextPage) && !posts.isFetchingNextPage && !posts.isFetchNextPageError,
    () => void posts.fetchNextPage(),
  )
  const deletePost = useDeletePost()
  const [editing, setEditing] = useState<Editing>(null)
  const [searchParams, setSearchParams] = useSearchParams()
  const creating = searchParams.get('new') === '1'

  if (session.isPending) return <p>Loading…</p>
  if (!session.data) return <Navigate to="/login" replace />

  const closeForm = () => {
    setEditing(null)
    setSearchParams({})
  }

  const list = posts.data?.pages.flat() ?? []
  const filtersActive = Boolean(filters.minRating || filters.search)

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <PostFilterBar filters={filters} onChange={(changes) => setFilters((current) => ({ ...current, ...changes }))} />

      {creating && <PostForm onDone={closeForm} />}

      {posts.isPending && <p className="text-muted-foreground">Loading posts…</p>}
      {posts.error && <p className="text-sm text-red-600">{posts.error.message}</p>}
      {posts.data && list.length === 0 && (
        <p className="text-muted-foreground">
          {filtersActive ? 'No posts match these filters.' : 'No posts yet. Add your first one.'}
        </p>
      )}

      <ul className="flex flex-col gap-6">
        {list.map((post) =>
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

      {posts.hasNextPage && <div ref={loadMoreRef} className="h-px" />}
      {posts.isFetchingNextPage && <p className="text-center text-sm text-muted-foreground">Loading more…</p>}
      {posts.isFetchNextPageError && (
        <div className="flex items-center justify-center gap-3 text-sm">
          <span className="text-muted-foreground">Couldn't load more posts.</span>
          <Button variant="outline" size="sm" onClick={() => void posts.fetchNextPage()}>
            Try again
          </Button>
        </div>
      )}
    </div>
  )
}
