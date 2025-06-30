from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import secrets
from sqlalchemy import select
from db.models import User, Referral

router = Router()

# 🚀 FSM states
class RegState(StatesGroup):
    first_name = State()
    last_name = State()

# 🚀 Reply tugmalar
def main_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="👥 Mening a’zolarim")],
            [types.KeyboardButton(text="ℹ️ Yordam")]
        ],
        resize_keyboard=True
    )

# 🚀 START
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, session):
    ref_code = message.text.split(' ', 1)[1] if ' ' in message.text else None

    existing_user = await session.get(User, message.from_user.id)
    if existing_user:
        link = f"https://t.me/Ref3ral_bot?start={existing_user.referral_code}"
        await message.answer(
            f"✅ Siz ro'yxatdan o'tgansiz.\nSizning referral link: {link}",
            reply_markup=main_menu()
        )
        return

    await state.update_data(ref_code=ref_code)
    await message.answer("👤 Iltimos, ismingizni kiriting:")
    await state.set_state(RegState.first_name)

# 🚀 FIRST NAME
@router.message(F.text.len() > 0, RegState.first_name)
async def reg_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("👤 Familiyangizni kiriting:")
    await state.set_state(RegState.last_name)

# 🚀 LAST NAME + DB saqlash + Referral
@router.message(F.text.len() > 0, RegState.last_name)
async def reg_last_name(message: types.Message, state: FSMContext, session):
    data = await state.get_data()
    referral_code = secrets.token_urlsafe(6)

    # Yangi user
    new_user = User(
        id=message.from_user.id,
        first_name=data["first_name"],
        last_name=message.text,
        referral_code=referral_code
    )
    session.add(new_user)
    await session.flush()

    # Referral bog‘lash
    if data.get("ref_code"):
        result = await session.execute(
            select(User).where(User.referral_code == data["ref_code"])
        )
        referrer = result.scalar_one_or_none()
        if referrer:
            session.add(Referral(user_id=new_user.id, referrer_id=referrer.id))

    await session.commit()
    await state.clear()

    link = f"https://t.me/Ref3ral_bot?start={referral_code}"
    await message.answer(
        f"🎉 Tabriklaymiz! Siz ro'yxatdan o'tdingiz.\n"
        f"Sizning referral link: {link}",
        reply_markup=main_menu()
    )

# 🚀 Mening a’zolarim
@router.message(F.text == "👥 Mening a’zolarim")
async def my_referrals(message: types.Message, session):
    result = await session.execute(
        select(User).join(Referral, User.id == Referral.user_id)
        .where(Referral.referrer_id == message.from_user.id)
    )
    referrals = result.scalars().all()

    if referrals:
        text = "👥 Sizning referral a'zolaringiz:\n"
        for u in referrals:
            text += f" - {u.first_name} {u.last_name}\n"
    else:
        text = "👥 Sizning referral a'zolaringiz hozircha yo'q."
    await message.answer(text)

# 🚀 Yordam
@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: types.Message):
    await message.answer(
        "ℹ️ Ushbu bot orqali referral link yaratib, do‘stlaringizni taklif qilishingiz mumkin.\n"
        "Referral link orqali kirgan do‘stlaringizni kuzatib boring."
    )
