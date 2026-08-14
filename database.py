import os
import sqlite3

# Railway'da doimiy volume /data ga ulangan. Lokal ishga tushirishda
# (kompyuterda) DB_PATH bo'lmasa, joriy papkadagi shop.db ishlatiladi.
DB_NAME = os.getenv("DB_PATH", "shop.db")

# Agar volume papkasi ko'rsatilgan bo'lsa, u mavjudligiga ishonch hosil qilamiz
_db_dir = os.path.dirname(DB_NAME)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT,
            photo_id TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    """)
    conn.commit()

    # Agar baza bo'sh bo'lsa - namuna ma'lumotlar qo'shamiz
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        seed_demo_data(conn)

    conn.close()


def seed_demo_data(conn):
    cur = conn.cursor()
    categories = ["Ichimliklar", "Fast-food", "Shirinliklar"]
    for name in categories:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    conn.commit()

    cur.execute("SELECT id, name FROM categories")
    cats = {row["name"]: row["id"] for row in cur.fetchall()}

    demo_products = [
        (cats["Ichimliklar"], "Coca-Cola 0.5L", 12000, "Sovuq gazlangan ichimlik"),
        (cats["Ichimliklar"], "Suv 0.5L", 4000, "Toza ichimlik suvi"),
        (cats["Fast-food"], "Burger", 25000, "Mol go'shtli burger"),
        (cats["Fast-food"], "Lavash", 22000, "Tovuqli lavash"),
        (cats["Shirinliklar"], "Tort bo'lagi", 18000, "Shokoladli tort"),
    ]
    for p in demo_products:
        cur.execute(
            "INSERT INTO products (category_id, name, price, description) VALUES (?, ?, ?, ?)",
            p,
        )
    conn.commit()


def get_categories():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return rows


def get_products_by_category(category_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE category_id = ?", (category_id,)
    ).fetchall()
    conn.close()
    return rows


def get_product(product_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    conn.close()
    return row


def add_product(category_id, name, price, description=""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO products (category_id, name, price, description) VALUES (?, ?, ?, ?)",
        (category_id, name, price, description),
    )
    conn.commit()
    conn.close()


def add_category(name):
    conn = get_conn()
    cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def delete_category(category_id):
    conn = get_conn()
    conn.execute("DELETE FROM products WHERE category_id = ?", (category_id,))
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_conn()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def update_product_price(product_id, new_price):
    conn = get_conn()
    conn.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
    conn.commit()
    conn.close()


def get_all_products():
    conn = get_conn()
    rows = conn.execute(
        "SELECT products.*, categories.name as category_name "
        "FROM products JOIN categories ON products.category_id = categories.id "
        "ORDER BY categories.name, products.name"
    ).fetchall()
    conn.close()
    return rows
