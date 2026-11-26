import { ChevronLeft, ChevronRight } from 'lucide-react'
import { photoUrl, type Post } from '@/api/posts'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'

type Image = Post['images'][number]

// Shows one photo of a post at full size, with buttons to move to the previous or next one.
// `index` is the photo being shown, or null when the viewer is closed.
export function PhotoViewer({
  postId,
  restaurantName,
  images,
  index,
  onIndexChange,
}: {
  postId: string
  restaurantName: string
  images: Image[]
  index: number | null
  onIndexChange: (index: number | null) => void
}) {
  const open = index !== null
  const current = index !== null ? images[index] : undefined
  const hasMany = images.length > 1

  return (
    <Dialog open={open} onOpenChange={(isOpen) => onIndexChange(isOpen ? 0 : null)}>
      <DialogContent className="max-w-3xl bg-background p-2">
        <DialogTitle className="sr-only">Photo of {restaurantName}</DialogTitle>
        {current && (
          <div className="relative">
            <img
              src={photoUrl(postId, current.id)}
              alt={`Photo of ${restaurantName}`}
              className="max-h-[80vh] w-full rounded-lg object-contain"
            />
            {hasMany && index !== null && (
              <div className="absolute inset-x-2 top-1/2 flex -translate-y-1/2 justify-between">
                <Button
                  variant="secondary"
                  size="icon"
                  aria-label="Previous photo"
                  disabled={index === 0}
                  onClick={() => onIndexChange(index - 1)}
                >
                  <ChevronLeft />
                </Button>
                <Button
                  variant="secondary"
                  size="icon"
                  aria-label="Next photo"
                  disabled={index === images.length - 1}
                  onClick={() => onIndexChange(index + 1)}
                >
                  <ChevronRight />
                </Button>
              </div>
            )}
          </div>
        )}
        {hasMany && index !== null && (
          <p className="text-center text-sm text-muted-foreground">
            {index + 1} / {images.length}
          </p>
        )}
      </DialogContent>
    </Dialog>
  )
}
