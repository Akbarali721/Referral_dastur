from aiogram import Router, types, F
from sqlalchemy import select, func
from db.models import User, Referral

router = Router()


def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("Mening a’zolarim"))
    return kb


def referral_list_kb(referrals):
    kb = types.InlineKeyboardMarkup()
    for ref in referrals:
        kb.add(types.InlineKeyboardButton(
            text=f"{ref.first_name} {ref.last_name}",
            callback_data=f"ref_{ref.id}"
        ))
    return kb


@router.message(F.text == "Mening a’zolarim")
async def my_referrals(message: types.Message, session):
    user_id = message.from_user.id

    # DEBUG QISM: referral jadvalidan to‘liq natijani tekshiramiz
    result = await session.execute(
        select(Referral).where(Referral.referrer_id == user_id)
    )
    referrals_raw = result.scalars().all()
    print(f"DEBUG: Referral list {referrals_raw}")
    print(f"DEBUG: Referral count {len(referrals_raw)}")

    # Asl so‘rov: referral foydalanuvchilarni olish
    result_users = await session.execute(
        select(User)
        .join(Referral, User.id == Referral.user_id)
        .where(Referral.referrer_id == user_id)
    )
    referrals = result_users.scalars().all()

    # Referral sonini hisoblash
    count = len(referrals_raw)

    # Xabar tayyorlash
    text = f"Sizning {count} ta referral a'zolaringiz bor.\n"

    if referrals:
        text += "\n".join(
            [f"{idx+1}. {r.first_name} {r.last_name or ''}".strip() for idx, r in enumerate(referrals)]
        )
    else:
        text += "Hozircha sizning referral a'zolaringiz yo'q."

    await message.answer(text)



@router.callback_query(F.data.startswith("ref_"))
async def referral_profile(callback: types.CallbackQuery, session):
    ref_id = int(callback.data.split("_")[1])
    user = await session.get(User, ref_id)

    if user:
        await callback.message.answer(
            f"👤 {user.first_name} {user.last_name}\nReferral code: {user.referral_code}"
        )
    else:
        await callback.message.answer("Foydalanuvchi topilmadi.")

    await callback.answer()
