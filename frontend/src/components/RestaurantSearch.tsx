import { useEffect, useRef, useState } from 'react'
import type { components } from '@/api/schema'
import { client } from '@/api/client'
import { Input } from '@/components/ui/input'
import { getLocation } from '@/lib/location'

export type Place = components['schemas']['PlaceResult']
type Suggestion = components['schemas']['Suggestion']

const PAUSE_MS = 300
const MIN_LETTERS = 3
const CLOSE_DELAY_MS = 150

// The restaurant name box.
// - Before typing: restaurants near the user.
// - While typing: suggestions for what's typed so far, with the nearest places first.
// Picking a suggestion looks up its details (city and cuisine) and hands them to the form.
export function RestaurantSearch({
  value,
  onChange,
  onPick,
}: {
  value: string
  onChange: (text: string) => void
  onPick: (place: Place) => void
}) {
  const [results, setResults] = useState<Suggestion[]>([])
  const [searching, setSearching] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState(false)
  // One session ID covers the typing and the pick, so Google bills them together.
  const session = useRef<string | null>(null)

  const query = value.trim()
  const typing = query.length >= MIN_LETTERS

  useEffect(() => {
    if (!open) return
    const controller = new AbortController()
    const timer = window.setTimeout(async () => {
      setSearching(true)
      try {
        const location = await getLocation()
        if (!typing && !location) {
          setSearched(true)
          setResults([])
          setError('Turn on location to see restaurants near you')
          return
        }

        const outcome =
          typing || !location
            ? await client.GET('/api/places/autocomplete', {
                params: { query: { q: query, session: session.current ?? undefined, ...(location ?? {}) } },
                signal: controller.signal,
              })
            : await client.GET('/api/places/nearby', {
                params: { query: { lat: location.lat, lng: location.lng } },
                signal: controller.signal,
              })

        setSearched(true)
        if (outcome.data) {
          setError(null)
          setResults(outcome.data)
        } else {
          setResults([])
          setError(outcome.response.status === 502 ? 'Search is unavailable right now' : 'Search failed')
        }
      } catch {
        // Ignored: the request was cancelled because the user kept typing.
      } finally {
        setSearching(false)
      }
    }, PAUSE_MS)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [query, typing, open])

  // Looks up the chosen place's details, then hands them to the form.
  async function pick(suggestion: Suggestion) {
    setOpen(false)
    setResults([])
    const { data, response } = await client.GET('/api/places/details/{place_id}', {
      params: { path: { place_id: suggestion.place_id }, query: { session: session.current ?? undefined } },
    })
    session.current = null
    if (data) {
      onPick(data)
    } else {
      setError(response.status === 502 ? 'Could not load that place. Type the details yourself.' : 'Could not load that place')
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <Input
        id="restaurant"
        required
        autoComplete="off"
        placeholder="Search for a restaurant"
        value={value}
        onFocus={() => {
          if (!session.current) session.current = crypto.randomUUID()
          setOpen(true)
          setSearched(false)
        }}
        onBlur={() => window.setTimeout(() => setOpen(false), CLOSE_DELAY_MS)}
        onChange={(event) => {
          // Typing starts a new search, so forget the old answer straight away.
          setOpen(true)
          setSearched(false)
          setError(null)
          onChange(event.target.value)
        }}
      />

      {open && (
        <ul className="flex flex-col overflow-hidden rounded-lg border bg-card">
          {!typing && results.length > 0 && (
            <li className="px-3 pt-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Near you</li>
          )}
          {searching && <li className="px-3 py-2 text-sm text-muted-foreground">Searching…</li>}
          {error && <li className="px-3 py-2 text-sm text-muted-foreground">{error}</li>}
          {results.map((suggestion) => (
            <li key={suggestion.place_id} className="border-b last:border-b-0">
              <button
                type="button"
                className="flex w-full flex-col items-start px-3 py-2 text-left hover:bg-muted"
                onClick={() => void pick(suggestion)}
              >
                <span className="font-medium">{suggestion.name}</span>
                <span className="text-sm text-muted-foreground">{suggestion.address}</span>
              </button>
            </li>
          ))}
          {searched && !searching && !error && results.length === 0 && (
            <li className="px-3 py-2 text-sm text-muted-foreground">No restaurants found. You can type the details yourself.</li>
          )}
        </ul>
      )}
    </div>
  )
}
