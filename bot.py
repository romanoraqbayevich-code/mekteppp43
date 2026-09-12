# -*- coding: utf-8 -*-
"""
Maktab dars jadvali va o'qituvchi/sinf qidirish boti.
TEST VERSIYA - data.py da namunaviy ma'lumotlar bilan ishlaydi.

Ishga tushirish:
    BOT_TOKEN=xxxx ADMIN_IDS=123456789 python bot.py
"""

import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import storage
from data import DAYS
from logic import (
    current_lesson_for_class,
    current_status_for_teacher,
    get_all_classes,
    get_all_teachers,
    get_class_schedule,
    get_teacher_classes,
    get_teacher_schedule,
    get_teacher_subject,
    now_tashkent,
    today_day_name,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = {
    int(x) for x in os.environ.get("ADMIN_IDS", "").replace(" ", "").split(",") if x
}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ---------------------------------------------------------------------------
# Klaviaturalar
# ---------------------------------------------------------------------------

def role_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👨‍🎓 O'quvchiman", callback_data="role:student")],
            [InlineKeyboardButton("👨‍🏫 O'qituvchiman", callback_data="role:teacher")],
        ]
    )


def classes_keyboard(prefix: str):
    buttons = [
        [InlineKeyboardButton(c, callback_data=f"{prefix}:{c}")]
        for c in get_all_classes()
    ]
    buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back:role")])
    return InlineKeyboardMarkup(buttons)


def teachers_keyboard(prefix: str, back_callback: str = "back:role"):
    buttons = [
        [InlineKeyboardButton(t, callback_data=f"{prefix}:{t}")]
        for t in get_all_teachers()
    ]
    buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data=back_callback)])
    return InlineKeyboardMarkup(buttons)


def student_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📅 Jadvalim", callback_data="stu:schedule")],
            [InlineKeyboardButton("🔍 O'qituvchini qidirish", callback_data="stu:search_teacher")],
            [InlineKeyboardButton("🔍 Sinfni qidirish", callback_data="stu:search_class")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:role")],
        ]
    )


def teacher_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📅 Jadvalim", callback_data="tea:schedule")],
            [InlineKeyboardButton("🏫 Qaysi sinflarda dars beraman", callback_data="tea:my_classes")],
            [InlineKeyboardButton("🔍 Boshqa o'qituvchini qidirish", callback_data="tea:search_teacher")],
            [InlineKeyboardButton("🔍 Sinfni qidirish", callback_data="tea:search_class")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:role")],
        ]
    )


def back_to_menu_keyboard(role: str):
    cb = "back:student_menu" if role == "student" else "back:teacher_menu"
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data=cb)]])


def day_keyboard(role: str):
    buttons, row = [], []
    for day in DAYS:
        row.append(InlineKeyboardButton(day, callback_data=f"day:{day}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    cb = "back:student_menu" if role == "student" else "back:teacher_menu"
    buttons.append([InlineKeyboardButton("⬅️ Menyuga qaytish", callback_data=cb)])
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Matn shakllantirish
# ---------------------------------------------------------------------------

def format_class_day(class_name: str, day: str, lessons):
    if not lessons:
        return f"📅 {class_name} sinf — {day}\n\nBu kuni dars yo'q."
    lines = [f"📅 {class_name} sinf — {day}\n"]
    for l in lessons:
        lines.append(f"⏰ {l['time']} | 📚 {l['subject']} | 👨‍🏫 {l['teacher']} | 🚪 {l['room']}-xona")
    return "\n".join(lines)


def format_teacher_day(teacher_name: str, subject: str, day: str, lessons):
    if not lessons:
        return f"📅 {teacher_name} ({subject}) — {day}\n\nBu kuni dars yo'q."
    lines = [f"📅 {teacher_name} ({subject}) — {day}\n"]
    for l in lessons:
        lines.append(f"⏰ {l['time']} | 🏫 {l['class']} sinf | 📚 {l['subject']} | 🚪 {l['room']}-xona")
    return "\n".join(lines)


def format_teacher_card(teacher_name: str):
    subject = get_teacher_subject(teacher_name)
    lesson, msg = current_status_for_teacher(teacher_name)
    now_str = now_tashkent().strftime("%H:%M")
    header = f"👨‍🏫 {teacher_name} — {subject} fani o'qituvchisi\n\n"
    if lesson:
        status = (
            f"🟢 Hozir ({now_str}): {lesson['class']} sinfda, "
            f"{lesson['subject']} darsida, {lesson['room']}-xonada\n\n"
        )
    else:
        status = f"🔴 Hozir ({now_str}): {msg}\n\n"

    schedule = get_teacher_schedule(teacher_name)
    lines = ["📋 Haftalik jadvali:"]
    for day in DAYS:
        day_lessons = schedule[day]
        if day_lessons:
            lines.append(f"\n{day}:")
            for l in day_lessons:
                lines.append(f"  ⏰ {l['time']} | 🏫 {l['class']} | 🚪 {l['room']}-xona")
    return header + status + "\n".join(lines)


def format_class_card(class_name: str):
    lesson, msg = current_lesson_for_class(class_name)
    now_str = now_tashkent().strftime("%H:%M")
    header = f"🏫 {class_name} sinf\n\n"
    if lesson:
        status = (
            f"🟢 Hozir ({now_str}): {lesson['subject']} darsida, "
            f"{lesson['teacher']} o'qituvchi, {lesson['room']}-xonada"
        )
    else:
        status = f"🔴 Hozir ({now_str}): {msg}"
    return header + status


# ---------------------------------------------------------------------------
# Umumiy komandalar
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    storage.register_user(chat_id)

    if storage.is_maintenance() and not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "🔧 Bot hozir texnik ishlar tufayli vaqtincha ishlamayapti. "
            "Iltimos, keyinroq urinib ko'ring."
        )
        return

    context.user_data.clear()
    await update.message.reply_text(
        "Assalomu alaykum! 👋\nKim sifatida kirmoqchisiz?",
        reply_markup=role_keyboard(),
    )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Sizning Telegram ID'ingiz: `{update.effective_user.id}`",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Buyruqlar:\n"
        "/start — botni boshlash\n"
        "/id — Telegram ID'ingizni ko'rish\n"
        "/admin — admin panel (faqat adminlar uchun)"
    )


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

def admin_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin:broadcast")],
            [InlineKeyboardButton("⏸ Texnik ishlar rejimi", callback_data="admin:maintenance")],
            [InlineKeyboardButton("📊 Statistika", callback_data="admin:stats")],
        ]
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Bu buyruq faqat adminlar uchun.")
        return
    await update.message.reply_text("🔧 Admin panel:", reply_markup=admin_keyboard())


async def handle_admin_callback(query, context: ContextTypes.DEFAULT_TYPE, data: str):
    if data == "admin:broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.edit_message_text(
            "✍️ Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing:"
        )
    elif data == "admin:maintenance":
        new_state = storage.toggle_maintenance()
        status_text = "🔴 YOQILDI (bot vaqtincha o'chirilgan)" if new_state else "🟢 O'CHIRILDI (bot ishlamoqda)"
        await query.edit_message_text(
            f"Texnik ishlar rejimi: {status_text}",
            reply_markup=admin_keyboard(),
        )
    elif data == "admin:stats":
        stats = storage.get_stats()
        lines = [f"📊 Statistika\n\n👥 Foydalanuvchilar soni: {stats['user_count']}\n"]
        if stats["action_counts"]:
            lines.append("📈 Funksiyalardan foydalanish:")
            for action, count in sorted(stats["action_counts"].items(), key=lambda x: -x[1]):
                lines.append(f"  • {action}: {count}")
        else:
            lines.append("Hali statistika yo'q.")
        await query.edit_message_text("\n".join(lines), reply_markup=admin_keyboard())


async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_broadcast"):
        return
    if not is_admin(update.effective_user.id):
        return

    context.user_data["awaiting_broadcast"] = False
    text = update.message.text
    users = storage.get_all_users()
    sent, failed = 0, 0
    for chat_id in users:
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"📢 E'lon:\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(
        f"✅ Xabar yuborildi.\nMuvaffaqiyatli: {sent}\nXato: {failed}"
    )


# ---------------------------------------------------------------------------
# Callback dispatcher
# ---------------------------------------------------------------------------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if storage.is_maintenance() and not is_admin(update.effective_user.id):
        await query.edit_message_text(
            "🔧 Bot hozir texnik ishlar tufayli vaqtincha ishlamayapti."
        )
        return

    if data.startswith("admin:"):
        if not is_admin(update.effective_user.id):
            await query.edit_message_text("⛔️ Ruxsat yo'q.")
            return
        await handle_admin_callback(query, context, data)
        return

    storage.log_action(data.split(":")[0] + ":" + data.split(":")[1] if ":" in data else data)

    # --- Rol tanlash ---
    if data == "role:student":
        context.user_data.clear()
        context.user_data["role"] = "student"
        await query.edit_message_text(
            "Sinfingizni tanlang:", reply_markup=classes_keyboard("class")
        )

    elif data == "role:teacher":
        context.user_data.clear()
        context.user_data["role"] = "teacher"
        await query.edit_message_text(
            "Ismingizni tanlang:", reply_markup=teachers_keyboard("teacher_login")
        )

    elif data.startswith("class:"):
        class_name = data.split(":", 1)[1]
        context.user_data["class"] = class_name
        context.user_data["role"] = "student"
        await query.edit_message_text(
            f"Xush kelibsiz, {class_name} sinf! 🎓", reply_markup=student_menu_keyboard()
        )

    elif data.startswith("teacher_login:"):
        teacher_name = data.split(":", 1)[1]
        context.user_data["teacher"] = teacher_name
        context.user_data["role"] = "teacher"
        await query.edit_message_text(
            f"Xush kelibsiz, {teacher_name}! 👋", reply_markup=teacher_menu_keyboard()
        )

    # --- O'quvchi menyusi ---
    elif data == "stu:schedule":
        class_name = context.user_data.get("class")
        context.user_data["viewing"] = {"type": "class", "id": class_name}
        day = today_day_name()
        if day is None:
            text = f"📅 {class_name} sinf\n\nBugun Yakshanba — dam olish kuni."
        else:
            lessons = get_class_schedule(class_name, day)
            text = format_class_day(class_name, day, lessons) + "\n\n(Bugungi kun avtomatik ko'rsatildi)"
        await query.edit_message_text(text, reply_markup=day_keyboard("student"))

    elif data == "stu:search_teacher" or data == "tea:search_teacher":
        role = context.user_data.get("role", "student")
        back_cb = "back:student_menu" if role == "student" else "back:teacher_menu"
        await query.edit_message_text(
            "O'qituvchini tanlang:", reply_markup=teachers_keyboard("search_teacher", back_cb)
        )

    elif data == "stu:search_class" or data == "tea:search_class":
        await query.edit_message_text(
            "Sinfni tanlang:", reply_markup=classes_keyboard("search_class")
        )

    # --- O'qituvchi menyusi ---
    elif data == "tea:schedule":
        teacher_name = context.user_data.get("teacher")
        context.user_data["viewing"] = {"type": "teacher", "id": teacher_name}
        subject = get_teacher_subject(teacher_name)
        day = today_day_name()
        if day is None:
            text = f"📅 {teacher_name}\n\nBugun Yakshanba — dam olish kuni."
        else:
            schedule = get_teacher_schedule(teacher_name)
            text = format_teacher_day(teacher_name, subject, day, schedule[day]) + "\n\n(Bugungi kun avtomatik ko'rsatildi)"
        await query.edit_message_text(text, reply_markup=day_keyboard("teacher"))

    elif data == "tea:my_classes":
        teacher_name = context.user_data.get("teacher")
        classes = get_teacher_classes(teacher_name)
        if classes:
            text = "🏫 Siz dars beradigan sinflar:\n\n" + "\n".join(f"• {c}" for c in classes)
        else:
            text = "Hozircha hech qanday sinfda darsingiz topilmadi."
        await query.edit_message_text(text, reply_markup=back_to_menu_keyboard("teacher"))

    # --- Qidiruv natijalari ---
    elif data.startswith("search_teacher:"):
        name = data.split(":", 1)[1]
        role = context.user_data.get("role", "student")
        await query.edit_message_text(format_teacher_card(name), reply_markup=back_to_menu_keyboard(role))

    elif data.startswith("search_class:"):
        name = data.split(":", 1)[1]
        role = context.user_data.get("role", "student")
        await query.edit_message_text(format_class_card(name), reply_markup=back_to_menu_keyboard(role))

    # --- Kun tanlash (jadval ichida) ---
    elif data.startswith("day:"):
        day = data.split(":", 1)[1]
        viewing = context.user_data.get("viewing", {})
        role = context.user_data.get("role", "student")
        if viewing.get("type") == "class":
            lessons = get_class_schedule(viewing["id"], day)
            text = format_class_day(viewing["id"], day, lessons)
        elif viewing.get("type") == "teacher":
            schedule = get_teacher_schedule(viewing["id"])
            subject = get_teacher_subject(viewing["id"])
            text = format_teacher_day(viewing["id"], subject, day, schedule[day])
        else:
            text = "Xatolik yuz berdi, /start bosing."
        await query.edit_message_text(text, reply_markup=day_keyboard(role))

    # --- Orqaga qaytish ---
    elif data == "back:role":
        context.user_data.clear()
        await query.edit_message_text("Kim sifatida kirmoqchisiz?", reply_markup=role_keyboard())

    elif data == "back:student_menu":
        await query.edit_message_text("Menyu:", reply_markup=student_menu_keyboard())

    elif data == "back:teacher_menu":
        await query.edit_message_text("Menyu:", reply_markup=teacher_menu_keyboard())


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable topilmadi. "
            "BotFather'dan olingan tokenni BOT_TOKEN sifatida bering."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_message))

    logger.info("Bot ishga tushdi (polling rejimida)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
