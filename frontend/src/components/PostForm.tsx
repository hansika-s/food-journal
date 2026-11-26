import { useState, type SubmitEvent } from 'react'
import {
  photoUrl,
  useCreatePost,
  useDeletePhoto,
  useUpdatePost,
  uploadPhoto,
  type Post,
} from '@/api/posts'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { RatingInput } from '@/components/RatingInput'
import { RestaurantSearch, type Place } from '@/components/RestaurantSearch'
import { cuisineFromTypes } from '@/lib/cuisine'

const MAX_PHOTOS = 5

// Creates a post when `post` is missing, or edits the given post.
export function PostForm({ post, onDone }: { post?: Post; onDone: () => void }) {
  const createPost = useCreatePost()
  const updatePost = useUpdatePost()
  const deletePhoto = useDeletePhoto()

  const [restaurantName, setRestaurantName] = useState(post?.restaurant.name ?? '')
  // The Google place picked from the search. Cleared when the name is typed by hand.
  const [placeId, setPlaceId] = useState<string | null>(null)
  const [city, setCity] = useState(post?.restaurant.city ?? '')
  const [cuisine, setCuisine] = useState(post?.restaurant.cuisine ?? '')
  const [rating, setRating] = useState<number | null>(post?.rating ?? null)
  const [items, setItems] = useState(post ? post.items.join(', ') : '')
  const [notes, setNotes] = useState(post?.notes ?? '')
  const [files, setFiles] = useState<File[]>([])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const existingPhotos = post?.images ?? []

  // Fills the city and cuisine from the picked place. Anything the place doesn't tell us stays as it was.
  function pickPlace(place: Place) {
    setRestaurantName(place.name)
    setPlaceId(place.place_id)
    if (place.city) setCity(place.city)
    const guessedCuisine = cuisineFromTypes(place.types)
    if (guessedCuisine) setCuisine(guessedCuisine)
  }

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (rating === null) {
      setError('Tap the stars to rate the place')
      return
    }
    if (existingPhotos.length + files.length > MAX_PHOTOS) {
      setError(`A post can have at most ${MAX_PHOTOS} photos`)
      return
    }

    setError(null)
    setSaving(true)
    const itemList = items.split(',').map((item) => item.trim()).filter(Boolean)
    try {
      let postId: string
      if (post) {
        await updatePost.mutateAsync({ id: post.id, changes: { restaurant_name: restaurantName, city, cuisine, place_id: placeId, rating, items: itemList, notes } })
        postId = post.id
      } else {
        const created = await createPost.mutateAsync({
          restaurant_name: restaurantName,
          city,
          cuisine,
          place_id: placeId,
          rating,
          items: itemList,
          notes,
        })
        postId = created.id
      }
      // Photos are uploaded one at a time, after the post itself is saved.
      for (const file of files) {
        await uploadPhoto(postId, file)
      }
      onDone()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Something went wrong')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{post ? 'Edit post' : 'New post'}</CardTitle>
      </CardHeader>

      <form onSubmit={handleSubmit}>
        <CardContent className="grid gap-5 sm:grid-cols-2">
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label htmlFor="restaurant">Restaurant</Label>
            <RestaurantSearch
              value={restaurantName}
              onChange={(text) => {
                setRestaurantName(text)
                setPlaceId(null)
              }}
              onPick={pickPlace}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="city">City</Label>
            <Input id="city" required value={city} onChange={(event) => setCity(event.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="cuisine">Cuisine</Label>
            <Input id="cuisine" required value={cuisine} onChange={(event) => setCuisine(event.target.value)} />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Your rating</Label>
            <RatingInput value={rating} onChange={setRating} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="items">What you had</Label>
            <Input id="items" placeholder="Ramen, gyoza, iced tea" value={items} onChange={(event) => setItems(event.target.value)} />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea id="notes" rows={3} value={notes} onChange={(event) => setNotes(event.target.value)} />
          </div>

          <div className="flex flex-col gap-3 sm:col-span-2">
            <Label>Photos</Label>
            {existingPhotos.length > 0 && (
              <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
                {existingPhotos.map((image) => (
                  <div key={image.id} className="flex flex-col gap-1">
                    <img src={photoUrl(post!.id, image.id)} alt={`Photo of ${post!.restaurant.name}`} className="aspect-square w-full rounded-md object-cover" />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="text-muted-foreground"
                      onClick={() => deletePhoto.mutate({ postId: post!.id, imageId: image.id })}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            )}
            {/* On a phone, "image/*" lets the user take a new photo with the camera or pick from the library. */}
            <Input id="photos" type="file" multiple accept="image/*" onChange={(event) => setFiles(Array.from(event.target.files ?? []))} />
            <p className="text-sm text-muted-foreground">
              Take a photo or choose from your library. Up to {MAX_PHOTOS} photos.
              {files.length > 0 && ` ${files.length} selected.`}
            </p>
          </div>

          {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        </CardContent>

        <CardFooter className="justify-end gap-2">
          <Button type="button" variant="outline" onClick={onDone}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? 'Saving…' : post ? 'Save changes' : 'Save post'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}
