import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN, ADMIN_ID
from database import init_db, get_categories, get_product
from keyboards import (
    main_menu_kb,
    categories_kb,
    products_kb,
    product_detail_kb,
    cart_kb,
    phone_request_kb,
    payment_kb,
    confirm_kb,
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

    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, order_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Admin'ga yuborishda xato: {e}")

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


async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
