from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Restaurant


def get_or_create_restaurant(db: Session, name: str, city: str, cuisine: str) -> Restaurant:
    city = city.strip().title()
    restaurant = db.scalar(
        select(Restaurant).where(
            func.lower(func.trim(Restaurant.name)) == name.strip().lower(),
            Restaurant.city == city,
        )
    )
    if restaurant is None:
        restaurant = Restaurant(name=name.strip(), city=city, cuisine=cuisine.strip())
        db.add(restaurant)
        db.flush()
    return restaurant
