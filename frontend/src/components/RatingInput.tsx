import { useState } from 'react'
import { Star } from 'lucide-react'
import { Input } from '@/components/ui/input'

// Rates a place. Tap the stars for whole or half points (tap the left half of a star for a half point),
// or type any value with one decimal place, such as 4.2, in the box.
export function RatingInput({ value, onChange }: { value: number | null; onChange: (value: number) => void }) {
  const shown = value ?? 0
  // The box keeps what was typed, so "4." stays "4." while the next digit is typed.
  const [text, setText] = useState(value === null ? '' : String(value))

  function pick(next: number) {
    setText(String(next))
    onChange(next)
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="inline-flex items-center gap-1" role="group" aria-label="Rating">
        {[0, 1, 2, 3, 4].map((index) => {
          const fillPercent = Math.min(Math.max(shown - index, 0), 1) * 100
          return (
            <span key={index} className="relative size-10">
              <Star className="absolute inset-0 size-10 text-muted-foreground/40" />
              <span className="absolute inset-y-0 left-0 overflow-hidden" style={{ width: `${fillPercent}%` }}>
                <Star className="size-10 fill-current text-primary" />
              </span>
              <button
                type="button"
                aria-label={`${index + 0.5} out of 5`}
                className="absolute inset-y-0 left-0 w-1/2"
                onClick={() => pick(index + 0.5)}
              />
              <button
                type="button"
                aria-label={`${index + 1} out of 5`}
                className="absolute inset-y-0 right-0 w-1/2"
                onClick={() => pick(index + 1)}
              />
            </span>
          )
        })}
      </div>
      <div className="flex items-center gap-2">
        <Input
          id="rating"
          type="number"
          inputMode="decimal"
          min="1"
          max="5"
          step="0.1"
          className="h-8 w-16 px-2 text-sm"
          aria-label="Rating value"
          value={text}
          onChange={(event) => {
            setText(event.target.value)
            const parsed = Number(event.target.value)
            // Only a valid value reaches the form. Partial input like "4." waits for the next digit.
            if (event.target.value !== '' && parsed >= 1 && parsed <= 5) onChange(Math.round(parsed * 10) / 10)
          }}
        />
        <span className="text-sm text-muted-foreground">/ 5</span>
      </div>
    </div>
  )
}
