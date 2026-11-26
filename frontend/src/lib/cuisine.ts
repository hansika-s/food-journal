// Google describes a place with types such as "indian_restaurant" or "cafe". This turns the first useful one
// into a cuisine name like "Indian". Returns an empty string when nothing fits, so the user types it instead.
const NOT_A_CUISINE = new Set(['restaurant', 'vegetarian', 'vegan', 'food', 'point_of_interest', 'establishment', 'store'])

export function cuisineFromTypes(types: string[]): string {
  for (const type of types) {
    const match = /^(.+)_restaurant$/.exec(type)
    if (match && !NOT_A_CUISINE.has(match[1])) {
      return capitalize(match[1].replace(/_/g, ' '))
    }
  }
  if (types.includes('cafe') || types.includes('coffee_shop')) return 'Cafe'
  if (types.includes('bakery')) return 'Bakery'
  return ''
}

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1)
}
