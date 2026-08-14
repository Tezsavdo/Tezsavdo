import sqlite3

DB_NAME = "shop.db"


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
