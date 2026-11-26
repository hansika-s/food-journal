import createClient, { type Middleware } from 'openapi-fetch'
import type { paths } from './schema'

// The CSRF token comes from the server (on login or session check). It's kept in memory, not in a cookie,
// so the server can tell that a change came from this app.
let csrfToken: string | null = null

export function setCsrfToken(token: string | null) {
  csrfToken = token
}

export function getCsrfToken(): string | null {
  return csrfToken
}

const WRITE_METHODS = ['POST', 'PATCH', 'PUT', 'DELETE']

// Runs before every request. Adds the CSRF header to changes, like our HTML pages do.
const csrfMiddleware: Middleware = {
  onRequest({ request }) {
    if (csrfToken && WRITE_METHODS.includes(request.method)) {
      request.headers.set('X-CSRF-Token', csrfToken)
    }
    return request
  },
}

// Relative URLs, so requests go to the same address the page came from. Vite forwards /api to FastAPI.
export const client = createClient<paths>({ baseUrl: '' })
client.use(csrfMiddleware)
