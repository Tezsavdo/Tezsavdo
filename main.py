import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN, ADMIN_ID, ADMIN_IDS
from database import (
    init_db,
    get_categories,
    get_product,
    add_category,
    add_product,
    delete_product,
    get_all_products,
)
from keyboards import (
    main_menu_kb,
    categories_kb,
    products_kb,
    product_detail_kb,
    cart_kb,
    phone_request_kb,
    payment_kb,
    confirm_kb,
    admin_menu_kb,
    admin_categories_kb,
    admin_products_delete_kb,
    admin_cancel_kb,
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# user_id -> {product_id: qty}
CARTS: dict[int, dict[int, int]] = {}


class Checkout(StatesGroup):
    name = State()
    phone = State()
    address = State()
    payment = State()
    confirm = State()


class AdminAddCategory(StatesGroup):
    name = State()


class AdminAddProduct(StatesGroup):
    category = State()
    name = State()
    price = State()
    description = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def get_cart(user_id: int) -> dict:
    return CARTS.setdefault(user_id, {})


def cart_total(user_id: int) -> int:
    total = 0
    for pid, qty in get_cart(user_id).items():
        p = get_product(pid)
        if p:
            total += p["price"] * qty
    return total


def cart_text(user_id: int) -> str:
    cart = get_cart(user_id)
    if not cart:
        return "🛒 Savatingiz bo'sh."
    lines = ["🛒 Sizning savatingiz:\n"]
    for pid, qty in cart.items():
        p = get_product(pid)
        if not p:
            continue
        lines.append(f"• {p['name']} x{qty} = {p['price'] * qty:,} so'm".replace(",", " "))
    lines.append(f"\n💰 Jami: {cart_total(user_id):,} so'm".replace(",", " "))
    return "\n".join(lines)


# ---------- START ----------

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! 👋\n"
        "Bizning dastavka botimizga xush kelibsiz.\n"
        "Quyidagi menyudan foydalaning:",
        reply_markup=main_menu_kb(),
    )


@dp.message(F.text == "ℹ️ Biz haqimizda")
async def about(message: Message):
    await message.answer(
        "Biz tez va sifatli dastavka xizmatini taqdim etamiz. 🚚\n"
        "Buyurtma berish uchun 'Katalog' bo'limidan foydalaning."
    )


# ---------- KATALOG ----------

@dp.message(F.text == "🛍 Katalog")
async def show_catalog(message: Message):
    if not get_categories():
        await message.answer("Hozircha kategoriyalar mavjud emas.")
        return
    await message.answer("Kategoriyani tanlang:", reply_markup=categories_kb())


@dp.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    category_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        "Mahsulotni tanlang:", reply_markup=products_kb(category_id)
    )
    await callback.answer()


@dp.callback_query(F.data == "back_cats")
async def back_to_categories(callback: CallbackQuery):
    await callback.message.edit_text("Kategoriyani tanlang:", reply_markup=categories_kb())
    await callback.answer()


@dp.callback_query(F.data.startswith("prod_"))
async def show_product_detail(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    p = get_product(product_id)
    if not p:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return
    text = f"<b>{p['name']}</b>\n\n{p['description'] or ''}\n\n💵 Narxi: {p['price']:,} so'm".replace(",", " ")
    await callback.message.edit_text(
        text, reply_markup=product_detail_kb(product_id, p["category_id"]), parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    cart = get_cart(callback.from_user.id)
    cart[product_id] = cart.get(product_id, 0) + 1
    await callback.answer("Savatga qo'shildi ✅")


# ---------- SAVAT ----------

@dp.message(F.text == "🛒 Savat")
async def show_cart(message: Message):
    cart = get_cart(message.from_user.id)
    if not cart:
        await message.answer(cart_text(message.from_user.id))
        return
    await message.answer(cart_text(message.from_user.id), reply_markup=cart_kb())


@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    CARTS[callback.from_user.id] = {}
    await callback.message.edit_text("🗑 Savat tozalandi.")
    await callback.answer()


# ---------- CHECKOUT (buyurtma berish) ----------

@dp.callback_query(F.data == "checkout")
async def checkout_start(callback: CallbackQuery, state: FSMContext):
    if not get_cart(callback.from_user.id):
        await callback.answer("Savat bo'sh!", show_alert=True)
        return
    await callback.message.answer("Ismingizni kiriting:")
    await state.set_state(Checkout.name)
    await callback.answer()


@dp.message(Checkout.name)
async def checkout_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "Telefon raqamingizni yuboring:", reply_markup=phone_request_kb()
    )
    await state.set_state(Checkout.phone)


@dp.message(Checkout.phone, F.contact)
async def checkout_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Yetkazib berish manzilingizni kiriting:", reply_markup=main_menu_kb())
    await state.set_state(Checkout.address)


@dp.message(Checkout.phone, F.text)
async def checkout_phone_text(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Yetkazib berish manzilingizni kiriting:", reply_markup=main_menu_kb())
    await state.set_state(Checkout.address)


@dp.message(Checkout.address)
async def checkout_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("To'lov usulini tanlang:", reply_markup=payment_kb())
    await state.set_state(Checkout.payment)


@dp.callback_query(Checkout.payment, F.data.startswith("pay_"))
async def checkout_payment(callback: CallbackQuery, state: FSMContext):
    payment = "Naqd pul" if callback.data == "pay_naqd" else "Karta orqali"
    await state.update_data(payment=payment)

    data = await state.get_data()
    user_id = callback.from_user.id
    summary = (
        f"📋 <b>Buyurtmangizni tekshiring:</b>\n\n"
        f"{cart_text(user_id)}\n\n"
        f"👤 Ism: {data['name']}\n"
        f"📱 Tel: {data['phone']}\n"
        f"📍 Manzil: {data['address']}\n"
        f"💳 To'lov: {payment}\n"
    )
    await callback.message.answer(summary, reply_markup=confirm_kb(), parse_mode="HTML")
    await state.set_state(Checkout.confirm)
    await callback.answer()


@dp.callback_query(Checkout.confirm, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    username = callback.from_user.username or "yo'q"

    order_text = (
        f"🆕 <b>YANGI BUYURTMA</b>\n\n"
        f"{cart_text(user_id)}\n\n"
        f"👤 Ism: {data['name']}\n"
        f"📱 Tel: {data['phone']}\n"
        f"📍 Manzil: {data['address']}\n"
        f"💳 To'lov: {data['payment']}\n"
        f"🔗 Username: @{username}\n"
        f"🆔 User ID: {user_id}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, order_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Admin'ga ({admin_id}) yuborishda xato: {e}")

    CARTS[user_id] = {}
    await state.clear()
    await callback.message.answer(
        "✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@dp.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Buyurtma bekor qilindi.", reply_markup=main_menu_kb())
    await callback.answer()


# ---------- ADMIN PANEL ----------

@dp.message(F.text == "/admin")
async def admin_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🛠 Admin panel:", reply_markup=admin_menu_kb())


@dp.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛠 Admin panel:", reply_markup=admin_menu_kb())
    await callback.answer()


# --- kategoriya qo'shish ---

@dp.callback_query(F.data == "admin_add_cat")
async def admin_add_cat_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "Yangi kategoriya nomini kiriting:", reply_markup=admin_cancel_kb()
    )
    await state.set_state(AdminAddCategory.name)
    await callback.answer()


@dp.message(AdminAddCategory.name)
async def admin_add_cat_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    add_category(message.text.strip())
    await state.clear()
    await message.answer(f"✅ Kategoriya qo'shildi: {message.text.strip()}", reply_markup=admin_menu_kb())


# --- mahsulot qo'shish ---

@dp.callback_query(F.data == "admin_add_prod")
async def admin_add_prod_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    if not get_categories():
        await callback.answer("Avval kategoriya qo'shing!", show_alert=True)
        return
    await callback.message.edit_text(
        "Qaysi kategoriyaga qo'shamiz?", reply_markup=admin_categories_kb()
    )
    await state.set_state(AdminAddProduct.category)
    await callback.answer()


@dp.callback_query(AdminAddProduct.category, F.data.startswith("admin_cat_"))
async def admin_add_prod_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])
    await state.update_data(category_id=category_id)
    await callback.message.edit_text(
        "Mahsulot nomini kiriting:", reply_markup=admin_cancel_kb()
    )
    await state.set_state(AdminAddProduct.name)
    await callback.answer()


@dp.message(AdminAddProduct.name)
async def admin_add_prod_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Narxini kiriting (so'mda, faqat raqam):", reply_markup=admin_cancel_kb())
    await state.set_state(AdminAddProduct.price)


@dp.message(AdminAddProduct.price)
async def admin_add_prod_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip().replace(" ", ""))
    except ValueError:
        await message.answer("❗️ Narxni faqat raqam ko'rinishida kiriting, masalan: 25000")
        return
    await state.update_data(price=price)
    await message.answer(
        "Mahsulot tavsifini kiriting (yoki '-' agar bo'lmasa):", reply_markup=admin_cancel_kb()
    )
    await state.set_state(AdminAddProduct.description)


@dp.message(AdminAddProduct.description)
async def admin_add_prod_description(message: Message, state: FSMContext):
    data = await state.get_data()
    description = "" if message.text.strip() == "-" else message.text.strip()
    add_product(data["category_id"], data["name"], data["price"], description)
    await state.clear()
    await message.answer(
        f"✅ Mahsulot qo'shildi: {data['name']} — {data['price']:,} so'm".replace(",", " "),
        reply_markup=admin_menu_kb(),
    )


# --- mahsulotlar ro'yxati ---

@dp.callback_query(F.data == "admin_list_prod")
async def admin_list_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    products = get_all_products()
    if not products:
        await callback.message.edit_text("Mahsulotlar mavjud emas.", reply_markup=admin_menu_kb())
        await callback.answer()
        return
    lines = ["📋 <b>Barcha mahsulotlar:</b>\n"]
    for p in products:
        price = f"{p['price']:,}".replace(",", " ")
        lines.append(f"• [{p['category_name']}] {p['name']} — {price} so'm")
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=admin_menu_kb(), parse_mode="HTML"
    )
    await callback.answer()


# --- mahsulot o'chirish ---

@dp.callback_query(F.data == "admin_del_prod")
async def admin_del_prod_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    if not get_all_products():
        await callback.answer("Mahsulotlar mavjud emas.", show_alert=True)
        return
    await callback.message.edit_text(
        "O'chirmoqchi bo'lgan mahsulotni tanlang:", reply_markup=admin_products_delete_kb()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_delprod_"))
async def admin_del_prod_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split("_")[-1])
    delete_product(product_id)
    await callback.message.edit_text("🗑 Mahsulot o'chirildi.", reply_markup=admin_menu_kb())
    await callback.answer()


async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
