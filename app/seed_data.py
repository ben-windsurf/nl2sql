import os, random, sqlite3, datetime as dt
from faker import Faker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "sample.db")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    fake = Faker()
    random.seed(42)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Tables
    cur.executescript("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        city TEXT,
        state TEXT,
        signup_date DATE
    );

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        name TEXT,
        category TEXT,
        price REAL
    );

    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        order_date DATE,
        status TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE order_items (
        order_item_id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        unit_price REAL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)

    # Seed customers
    customers = []
    for i in range(1, 301):
        first = fake.first_name()
        last = fake.last_name()
        email = f"{first.lower()}.{last.lower()}@example.com"
        city = fake.city()
        state = fake.state_abbr()
        signup = fake.date_between(start_date="-3y", end_date="today")
        customers.append((i, first, last, email, city, state, signup))
    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)", customers)

    # Seed products
    categories = ["Electronics", "Home", "Outdoors", "Clothing", "Toys", "Books"]
    products = []
    for i in range(1, 201):
        name = f"Product {i}"
        category = random.choice(categories)
        price = round(random.uniform(5, 500), 2)
        products.append((i, name, category, price))
    cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)

    # Seed orders & items
    order_id = 1
    order_items_id = 1
    statuses = ["pending", "shipped", "delivered", "cancelled"]
    for _ in range(2000):
        cust_id = random.randint(1, 300)
        order_date = fake.date_between(start_date="-2y", end_date="today")
        status = random.choices(statuses, weights=[0.2,0.4,0.35,0.05])[0]
        cur.execute("INSERT INTO orders (order_id, customer_id, order_date, status) VALUES (?, ?, ?, ?)", (order_id, cust_id, order_date, status))

        # 1-5 items per order
        for _ in range(random.randint(1,5)):
            prod_id = random.randint(1, 200)
            qty = random.randint(1, 4)
            # Price can drift slightly from product base price
            base_price = next(p[3] for p in products if p[0] == prod_id)
            unit_price = round(base_price * random.uniform(0.9, 1.1), 2)
            cur.execute(
                "INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
                (order_items_id, order_id, prod_id, qty, unit_price)
            )
            order_items_id += 1

        order_id += 1

    conn.commit()
    conn.close()
    print(f"Seeded DB at {DB_PATH}")

if __name__ == "__main__":
    main()
