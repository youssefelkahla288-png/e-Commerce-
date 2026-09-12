"""
create_database.py — builds ecommerce.db from scratch and fills it with fake data.

Run this ONCE:  python -m scripts.create_database
It is safe to re-run: it deletes and rebuilds the tables each time.
"""

import sqlite3
import random

from faker import Faker

from app.config import settings

fake = Faker()

# ---- The "menu" of fake data we'll build products from ----
CATEGORIES = [
    ("Smartphones", "Mobile phones and accessories"),
    ("Laptops", "Portable computers"),
    ("Headphones", "Audio listening devices"),
    ("Tablets", "Handheld touchscreen devices"),
    ("Smartwatches", "Wearable smart devices"),
]

BRANDS = [
    ("Apple", "Premium consumer electronics"),
    ("Samsung", "Global electronics maker"),
    ("Sony", "Audio and multimedia electronics"),
    ("Dell", "Computers and laptops"),
    ("Bose", "High-end audio equipment"),
]

ORDER_STATUSES = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]

# Human-readable singular of each category, so product names read as "Apple Laptop"
# instead of the clumsy "Apple Laptops" or a wrongly chopped "Bose Smartwatche".
CATEGORY_SINGULAR = {
    "Smartphones": "Smartphone",
    "Laptops": "Laptop",
    "Headphones": "Headphones",
    "Tablets": "Tablet",
    "Smartwatches": "Smartwatch",
}


def create_tables(cur):
    """Create our four tables. We DROP first so re-running gives a clean slate."""
    cur.executescript(
        """
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS brands;
        DROP TABLE IF EXISTS categories;

        CREATE TABLE categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE brands (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE products (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT NOT NULL,
            description    TEXT,
            category_id    INTEGER,
            brand_id       INTEGER,
            price          REAL,
            stock_quantity INTEGER,
            rating         REAL,
            num_reviews    INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (brand_id)    REFERENCES brands(id)
        );

        -- We keep orders simple: one product per order, with the customer's name
        -- stored directly. That makes "order status" queries easy to read.
        CREATE TABLE orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            product_id    INTEGER,
            quantity      INTEGER,
            total_amount  REAL,
            status        TEXT,
            order_date    TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        """
    )


def seed_lookup_tables(cur):
    """Fill the small, fixed tables: categories and brands."""
    cur.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", CATEGORIES)
    cur.executemany("INSERT INTO brands (name, description) VALUES (?, ?)", BRANDS)


def seed_products(cur, how_many=40):
    """Create fake products by mixing a random brand with a random category."""
    cur.execute("SELECT id, name FROM categories")
    categories = cur.fetchall()               # list of (id, name)
    cur.execute("SELECT id, name FROM brands")
    brands = cur.fetchall()

    products = []
    for _ in range(how_many):
        cat_id, cat_name = random.choice(categories)
        brand_id, brand_name = random.choice(brands)
        single = CATEGORY_SINGULAR.get(cat_name, cat_name)
        products.append((
            f"{brand_name} {single}",                        # e.g. "Apple Laptop"
            f"A {single.lower()} made by {brand_name}",
            cat_id,
            brand_id,
            round(random.uniform(80, 2000), 2),              # price
            random.randint(0, 200),                          # stock
            round(random.uniform(3.5, 5.0), 1),              # rating
            random.randint(5, 400),                          # number of reviews
        ))

    cur.executemany(
        """INSERT INTO products
           (name, description, category_id, brand_id, price, stock_quantity, rating, num_reviews)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        products,
    )


def seed_orders(cur, how_many=30):
    """Create fake orders, each pointing at a real product."""
    cur.execute("SELECT id, price FROM products")
    products = cur.fetchall()                 # list of (id, price)

    orders = []
    for _ in range(how_many):
        product_id, price = random.choice(products)
        quantity = random.randint(1, 3)
        orders.append((
            fake.name(),                       # customer_name
            product_id,
            quantity,
            round(price * quantity, 2),        # total_amount
            random.choice(ORDER_STATUSES),
            fake.date_between(start_date="-6M", end_date="today").isoformat(),
        ))

    cur.executemany(
        """INSERT INTO orders
           (customer_name, product_id, quantity, total_amount, status, order_date)
           VALUES (?, ?, ?, ?, ?, ?)""",
        orders,
    )


def main():
    # sqlite3.connect creates the file if it doesn't exist.
    connection = sqlite3.connect(settings.db_path)
    cursor = connection.cursor()

    create_tables(cursor)
    seed_lookup_tables(cursor)
    seed_products(cursor)
    seed_orders(cursor)

    connection.commit()   # save all changes
    connection.close()
    print(f"✅ Database created at {settings.db_path}")


if __name__ == "__main__":
    main()