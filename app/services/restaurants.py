from uuid import UUID

from sqlalchemy import delete, exists, func, select
from sqlalchemy.orm import Session

from app.models import Post, Restaurant


# Finds the restaurant for a place, or creates it. A Google place ID is the exact match, so it is tried first.
# Without one (a restaurant typed by hand), the name and city are used. A restaurant found by name that has no
# place ID yet gets this one, so the next lookup matches exactly.
def get_or_create_restaurant(
    db: Session, name: str, city: str, cuisine: str, place_id: str | None = None
) -> Restaurant:
    city = city.strip().title()
    restaurant = None
    if place_id:
        restaurant = db.scalar(select(Restaurant).where(Restaurant.google_place_id == place_id))
    if restaurant is None:
        # A name match is only used when it can't be a different place: a restaurant that already has
        # another place ID is left alone.
        by_name = select(Restaurant).where(
            func.lower(func.trim(Restaurant.name)) == name.strip().lower(),
            Restaurant.city == city,
        )
        if place_id:
            by_name = by_name.where(Restaurant.google_place_id.is_(None))
        restaurant = db.scalar(by_name)
        if restaurant is not None and place_id:
            restaurant.google_place_id = place_id
    if restaurant is None:
        restaurant = Restaurant(name=name.strip(), city=city, cuisine=cuisine.strip(), google_place_id=place_id)
        db.add(restaurant)
        db.flush()
    return restaurant


# Deletes restaurants that no post uses any more. Call it with the restaurants a change may have left unused.
def delete_unused_restaurants(db: Session, restaurant_ids: set[UUID]) -> None:
    for restaurant_id in restaurant_ids:
        if not db.scalar(select(exists().where(Post.restaurant_id == restaurant_id))):
            db.execute(delete(Restaurant).where(Restaurant.id == restaurant_id))
    db.commit()
