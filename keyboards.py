from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from database import get_categories, get_products_by_category


def main_menu_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Katalog"), KeyboardButton(text="🛒 Savat")],
            [KeyboardButton(text="ℹ️ Biz haqimizda")],
        ],
        resize_keyboard=True,
    )
    return kb


def categories_kb():
    builder = []
    for cat in get_categories():
        builder.append(
            [InlineKeyboardButton(text=cat["name"], callback_data=f"cat_{cat['id']}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=builder)


def products_kb(category_id):
    builder = []
    for p in get_products_by_category(category_id):
        text = f"{p['name']} — {p['price']:,} so'm".replace(",", " ")
        builder.append(
            [InlineKeyboardButton(text=text, callback_data=f"prod_{p['id']}")]
        )
    builder.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_cats")])
    return InlineKeyboardMarkup(inline_keyboard=builder)


def product_detail_kb(product_id, category_id):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Savatga qo'shish", callback_data=f"add_{product_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"cat_{category_id}")],
        ]
    )
    return kb


def cart_kb():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="checkout")],
            [InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="clear_cart")],
        ]
    )
    return kb


def phone_request_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return kb


def payment_kb():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💵 Naqd pul", callback_data="pay_naqd")],
            [InlineKeyboardButton(text="💳 Karta orqali", callback_data="pay_karta")],
        ]
    )
    return kb


def confirm_kb():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")],
        ]
    )
    return kb


# ---------- ADMIN PANEL ----------

def admin_menu_kb():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📂 Kategoriya qo'shish", callback_data="admin_add_cat")],
            [InlineKeyboardButton(text="➕ Mahsulot qo'shish", callback_data="admin_add_prod")],
            [InlineKeyboardButton(text="📋 Mahsulotlar ro'yxati", callback_data="admin_list_prod")],
            [InlineKeyboardButton(text="🗑 Mahsulot o'chirish", callback_data="admin_del_prod")],
        ]
    )
    return kb


def admin_categories_kb(prefix="admin_cat_"):
    builder = []
    for cat in get_categories():
        builder.append(
            [InlineKeyboardButton(text=cat["name"], callback_data=f"{prefix}{cat['id']}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=builder)


def admin_products_delete_kb():
    builder = []
    for p in get_all_products_local():
        text = f"{p['name']} ({p['category_name']})"
        builder.append(
            [InlineKeyboardButton(text=text, callback_data=f"admin_delprod_{p['id']}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=builder)


def get_all_products_local():
    from database import get_all_products
    return get_all_products()


def admin_cancel_kb():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel")],
        ]
    )
    return kb
