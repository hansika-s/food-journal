export type Coordinates = { lat: number; lng: number }

let location: Promise<Coordinates | null> | null = null

// Asks the browser for the user's location once per page load. Resolves to null when the user says no,
// or when the browser can't tell. The app works without it, just without nearby results.
export function getLocation(): Promise<Coordinates | null> {
  location ??= new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null)
      return
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve({ lat: position.coords.latitude, lng: position.coords.longitude }),
      () => resolve(null),
      { timeout: 8000, maximumAge: 10 * 60 * 1000 },
    )
  })
  return location
}
