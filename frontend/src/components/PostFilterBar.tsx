import { useEffect, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import type { PostFilters } from '@/api/posts'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const RATING_OPTIONS: { label: string; minRating?: number }[] = [
  { label: 'All ratings' },
  { label: '3 and up', minRating: 3 },
  { label: '4 and up', minRating: 4 },
  { label: '5 only', minRating: 5 },
]

const PAUSE_MS = 300

// Search and rating filter on one row. The search waits a moment after typing stops before it asks the server.
export function PostFilterBar({
  filters,
  onChange,
}: {
  filters: PostFilters
  onChange: (changes: Partial<PostFilters>) => void
}) {
  const [text, setText] = useState(filters.search ?? '')
  const current = RATING_OPTIONS.find((option) => option.minRating === filters.minRating) ?? RATING_OPTIONS[0]

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const search = text.trim() || undefined
      if (search !== filters.search) onChange({ search })
    }, PAUSE_MS)
    return () => window.clearTimeout(timer)
  }, [text, filters.search, onChange])

  return (
    <div className="flex items-center justify-between gap-3">
      <Input
        type="search"
        aria-label="Search posts"
        placeholder="Search restaurants, cities, cuisines"
        value={text}
        onChange={(event) => setText(event.target.value)}
        className="h-9 max-w-xs"
      />
      <DropdownMenu>
        <DropdownMenuTrigger className="flex shrink-0 items-center gap-1 rounded-full border px-3 py-1 text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50">
          {current.label}
          <ChevronDown className="size-3.5" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-40">
          {RATING_OPTIONS.map((option) => (
            <DropdownMenuItem key={option.label} onClick={() => onChange({ minRating: option.minRating })}>
              {option.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
