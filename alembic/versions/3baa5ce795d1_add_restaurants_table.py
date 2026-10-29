"""add restaurants table

Revision ID: 3baa5ce795d1
Revises: 17dfc4866113
Create Date: 2026-10-29 12:06:11.232059

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3baa5ce795d1'
down_revision: Union[str, Sequence[str], None] = '17dfc4866113'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('restaurants',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('city', sa.String(), nullable=False),
    sa.Column('cuisine', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.execute(
        """
        INSERT INTO restaurants (id, name, city, cuisine, created_at)
        SELECT DISTINCT ON (lower(trim(restaurant_name)), initcap(trim(city)))
            gen_random_uuid(), trim(restaurant_name), initcap(trim(city)), cuisine, created_at
        FROM posts
        ORDER BY lower(trim(restaurant_name)), initcap(trim(city)), created_at
        """
    )
    op.add_column('posts', sa.Column('restaurant_id', sa.Uuid(), nullable=True))
    op.execute(
        """
        UPDATE posts
        SET restaurant_id = restaurants.id
        FROM restaurants
        WHERE lower(trim(restaurants.name)) = lower(trim(posts.restaurant_name))
          AND restaurants.city = initcap(trim(posts.city))
        """
    )
    op.alter_column('posts', 'restaurant_id', nullable=False)
    op.create_foreign_key('fk_posts_restaurant_id', 'posts', 'restaurants', ['restaurant_id'], ['id'])
    op.drop_column('posts', 'city')
    op.drop_column('posts', 'cuisine')
    op.drop_column('posts', 'restaurant_name')


def downgrade() -> None:
    op.add_column('posts', sa.Column('restaurant_name', sa.VARCHAR(), nullable=True))
    op.add_column('posts', sa.Column('cuisine', sa.VARCHAR(), nullable=True))
    op.add_column('posts', sa.Column('city', sa.VARCHAR(), nullable=True))
    op.execute(
        """
        UPDATE posts
        SET restaurant_name = restaurants.name,
            cuisine = restaurants.cuisine,
            city = restaurants.city
        FROM restaurants
        WHERE restaurants.id = posts.restaurant_id
        """
    )
    op.alter_column('posts', 'restaurant_name', nullable=False)
    op.alter_column('posts', 'cuisine', nullable=False)
    op.alter_column('posts', 'city', nullable=False)
    op.drop_constraint('fk_posts_restaurant_id', 'posts', type_='foreignkey')
    op.drop_column('posts', 'restaurant_id')
    op.drop_table('restaurants')
