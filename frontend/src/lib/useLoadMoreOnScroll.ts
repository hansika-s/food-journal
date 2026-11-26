import { useEffect, useRef, useState } from 'react'

// Calls onLoadMore when the marker at the bottom of a list comes close to the screen.
// Attach the returned function as the marker's ref. Calls stop while `enabled` is false.
export function useLoadMoreOnScroll(enabled: boolean, onLoadMore: () => void) {
  // State, so the effect re-runs once the marker element appears.
  const [marker, setMarker] = useState<Element | null>(null)
  // Always the latest callback, without reconnecting the observer on every render.
  const latest = useRef(onLoadMore)
  useEffect(() => {
    latest.current = onLoadMore
  })

  useEffect(() => {
    if (!enabled || !marker) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) latest.current()
      },
      // Start loading a little before the marker is actually on screen.
      { rootMargin: '0px 0px 600px 0px' },
    )
    observer.observe(marker)
    return () => observer.disconnect()
  }, [enabled, marker])

  return setMarker
}
