import { Star } from 'lucide-react'

// Shows a rating as five stars. A partly filled star shows a decimal, so 4.5 fills four stars and half of the fifth.
export function RatingStars({ value }: { value: number }) {
  return (
    <div className="inline-flex items-center gap-0.5" role="img" aria-label={`${value} out of 5 stars`}>
      {[0, 1, 2, 3, 4].map((index) => {
        const fillPercent = Math.min(Math.max(value - index, 0), 1) * 100
        return (
          <span key={index} className="relative size-4">
            {/* The empty star underneath, in a muted color. */}
            <Star className="absolute inset-0 size-4 text-muted-foreground/40" />
            {/* The filled star, clipped to the fraction that should be filled. */}
            <span className="absolute inset-y-0 left-0 overflow-hidden" style={{ width: `${fillPercent}%` }}>
              <Star className="size-4 fill-current text-primary" />
            </span>
          </span>
        )
      })}
    </div>
  )
}
