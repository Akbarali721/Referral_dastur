from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from sqlalchemy import select, func, desc
from aiogram.types import BufferedInputFile
from aiogram.enums.parse_mode import ParseMode
from db.session import async_session
from db.models import User, Referral
from config import ADMINS
import openpyxl
import io
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

router = Router()



# 🎛️ Inline tugmalar
stats_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📈 Umumiy foydalanuvchilar", callback_data="total_users")],
    [InlineKeyboardButton(text="🔗 Referral orqali kirganlar", callback_data="referred_users")],
    [InlineKeyboardButton(text="🏆 TOP 10 referallar", callback_data="top_referrals")],
    [InlineKeyboardButton(text="📆 Kunlik referallar", callback_data="daily_referrals")],
    [InlineKeyboardButton(text="📊 Grafik (7 kun)", callback_data="weekly_graph")],
    [InlineKeyboardButton(text="📥 Excel yuklab olish", callback_data="export_excel")]
])


# 🔘 Statistika tugmasi
@router.message(F.text.lower() == "📊 statistika")
async def show_stats(message: Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("⛔ Sizga ruxsat berilmagan.")
    await message.answer("📊 Qaysi statistikani ko‘rmoqchisiz?", reply_markup=stats_kb)

# 👥 Umumiy foydalanuvchilar
@router.callback_query(F.data == "total_users")
async def total_users(call: CallbackQuery):
    async with async_session() as session:
        total = await session.scalar(select(func.count(User.id)))
    await call.message.answer(f"👥 Umumiy foydalanuvchilar soni: <b>{total}</b>",parse_mode=ParseMode.HTML)
    await call.answer()

# 🔗 Referral orqali kirganlar
@router.callback_query(F.data == "referred_users")
async def referred_users(call: CallbackQuery):
    async with async_session() as session:
        referred = await session.scalar(select(func.count()).where(User.referred_by.isnot(None)))
    await call.message.answer(f"🔗 Referral orqali kirganlar soni: <b>{referred}</b>",parse_mode=ParseMode.HTML)
    await call.answer()

# 🏆 TOP 10 referrerlar
@router.callback_query(F.data == "top_referrals")
async def top_referrals(call: CallbackQuery):
    async with async_session() as session:
        stmt = (
            select(User.first_name, func.count(Referral.id).label("ref_count"))
            .join(Referral, Referral.referrer_id == User.id)
            .group_by(User.id)
            .order_by(desc("ref_count"))
            .limit(10)
        )
        results = await session.execute(stmt)
        rows = results.all()

    text = "🏆 <b>Top 10 referal foydalanuvchilar:</b>\n\n"
    for i, row in enumerate(rows, start=1):
        name, count = row
        text += f"{i}. {name}: <b>{count}</b> ta\n"

    await call.message.answer(text,parse_mode=ParseMode.HTML)
    await call.answer()

# 📆 So‘nggi 24 soat
@router.callback_query(F.data == "daily_referrals")
async def daily_referrals(call: CallbackQuery):
    async with async_session() as session:
        since = datetime.utcnow() - timedelta(days=1)
        count = await session.scalar(select(func.count()).where(Referral.created_at >= since))
    await call.message.answer(f"📆 So‘nggi 24 soat ichida referal orqali kirganlar: <b>{count}</b>",parse_mode=ParseMode.HTML)
    await call.answer()

# 📊 Grafik ko‘rinishida 7 kunlik statistika
@router.callback_query(F.data == "weekly_graph")
async def weekly_referrals_graph(call: CallbackQuery):
    async with async_session() as session:
        today = datetime.utcnow().date()
        counts = []

        for i in range(7):
            day = today - timedelta(days=6 - i)
            next_day = day + timedelta(days=1)

            stmt = select(func.count()).where(
                Referral.created_at >= datetime.combine(day, datetime.min.time()),
                Referral.created_at < datetime.combine(next_day, datetime.min.time())
            )
            count = await session.scalar(stmt)
            counts.append((day.strftime("%b %d"), count))

    # Matplotlib bilan grafik yasash
    dates, values = zip(*counts)
    plt.figure(figsize=(10, 5))
    plt.bar(dates, values, color='skyblue')
    plt.title("🗓️ So‘nggi 7 kunlik referallar soni")
    plt.xlabel("Sana")
    plt.ylabel("Referallar")
    plt.xticks(rotation=30)
    plt.tight_layout()
    chart_path = "weekly_chart.png"
    plt.savefig(chart_path)
    plt.close()

    # Telegramga rasm yuborish
    photo = FSInputFile(chart_path)
    await call.message.answer_photo(photo, caption="📊 So‘nggi 7 kunlik referal statistikasi")
    await call.answer()

    # Faylni tozalash
    os.remove(chart_path)


@router.callback_query(F.data == "export_excel")
async def export_excel(call: CallbackQuery):
    async with async_session() as session:
        stmt = (
            select(User.id, User.first_name, User.last_name, User.referral_code, User.referred_by)
            .order_by(User.id)
        )
        results = await session.execute(stmt)
        rows = results.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Foydalanuvchilar"

    headers = ["ID", "Ismi", "Familiyasi", "Referral KOD", "Taklif qilgan ID"]
    ws.append(headers)

    for row in rows:
        ws.append(list(row))

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    file = BufferedInputFile(buffer.read(), filename=f"referal-statistika-{datetime.now().date()}.xlsx")

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_menu")]
    ])

    await call.message.answer_document(file, caption="📥 Excel fayl tayyor!", reply_markup=buttons)
