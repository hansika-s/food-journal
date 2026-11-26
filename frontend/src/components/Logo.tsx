import { Link } from 'react-router'

// The app's wordmark: two heavy lines, set tight, in the main color. Tapping it goes to the home page.
export function Logo() {
  return (
    <h1 className="mb-6 font-logo text-3xl leading-[0.95] tracking-tight text-primary">
      <Link to="/" className="text-inherit no-underline">
        food
        <br />
        journal
      </Link>
    </h1>
  )
}
