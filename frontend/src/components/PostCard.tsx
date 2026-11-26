import { useState } from 'react'
import { Utensils } from 'lucide-react'
import { photoUrl, type Post } from '@/api/posts'
import { Button } from '@/components/ui/button'
import { PhotoViewer } from '@/components/PhotoViewer'

// One post, as a compact row: the cover photo (with a count when there are more), then the restaurant, the rating,
// what you had, and the notes. Tapping the photo opens all of them full size.
export function PostCard({ post, onEdit, onDelete }: { post: Post; onEdit: () => void; onDelete: () => void }) {
  const [viewing, setViewing] = useState<number | null>(null)
  const [cover, ...others] = post.images

  return (
    <li className="flex gap-4 border-b py-4">
      {cover ? (
        <button type="button" className="relative block h-36 w-28 shrink-0 overflow-hidden rounded-lg" onClick={() => setViewing(0)} aria-label="View photos">
          <img
            src={photoUrl(post.id, cover.id)}
            alt={`Photo of ${post.restaurant.name}`}
            className="block h-full w-full object-cover"
          />
          {others.length > 0 && (
            <span className="absolute bottom-2 right-2 rounded-full bg-background/90 px-2.5 py-1 text-xs font-medium">
              +{others.length}
            </span>
          )}
        </button>
      ) : (
        <div className="flex h-36 w-28 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
          <Utensils className="size-5" />
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="truncate font-medium">{post.restaurant.name}</h3>
          <span className="shrink-0 text-sm">{post.rating} / 5</span>
        </div>
        <p className="text-sm text-muted-foreground">
          {post.restaurant.city} · {post.restaurant.cuisine}
        </p>

        {post.items.length > 0 && (
          <p className="text-sm">
            <span className="text-muted-foreground">Had </span>
            {post.items.join(', ')}
          </p>
        )}

        {post.notes && <p className="line-clamp-2 text-sm text-muted-foreground">{post.notes}</p>}

        <div className="mt-1 flex items-center gap-3 text-sm">
          <Button variant="link" className="h-auto p-0 text-sm" onClick={onEdit}>
            Edit
          </Button>
          <Button variant="link" className="h-auto p-0 text-sm text-muted-foreground" onClick={onDelete}>
            Delete
          </Button>
        </div>
      </div>

      <PhotoViewer
        postId={post.id}
        restaurantName={post.restaurant.name}
        images={post.images}
        index={viewing}
        onIndexChange={setViewing}
      />
    </li>
  )
}
