import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# ─── تنظیمات ───────────────────────────────────────────────
BOT_TOKEN = "اینجا توکن ربات تلگرامت رو بذار"
OPENROUTER_API_KEY = "اینجا API Key اوپن‌روتر رو بذار"

MODEL = "meta-llama/llama-3.3-8b-instruct:free"

SYSTEM_PROMPT = """تو یک دستیار هوشمند فارسی زبان هستی به نام ParsMind.
همیشه به فارسی جواب بده مگر اینکه کاربر به زبان دیگه‌ای بنویسه.
مودب، مفید و صادق باش."""

# ─── لاگ ───────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── حافظه مکالمه هر کاربر ─────────────────────────────────
user_histories = {}

def ask_ai(user_id: int, user_message: str) -> str:
    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    # نگه‌داشتن فقط ۲۰ پیام آخر
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT}
                ] + user_histories[user_id],
                "max_tokens": 1000,
            },
            timeout=30
        )
        result = response.json()
        reply = result["choices"][0]["message"]["content"]

        user_histories[user_id].append({
            "role": "assistant",
            "content": reply
        })

        return reply

    except Exception as e:
        logger.error(f"خطا: {e}")
        return "⚠️ متأسفم، یه مشکلی پیش اومد. دوباره امتحان کن."


# ─── هندلرها ───────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name} عزیز! 👋\n\n"
        "من ParsMind هستم، دستیار هوشمند فارسی‌زبان شما 🤖\n\n"
        "هر سوالی داری بپرس!\n\n"
        "📌 دستورات:\n"
        "/new — شروع مکالمه جدید\n"
        "/help — راهنما"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 راهنمای ParsMind\n\n"
        "• هر چیزی بپرسی جواب می‌دم\n"
        "• تاریخچه مکالمه رو به خاطر می‌سپارم\n"
        "• /new بزن تا مکالمه از صفر شروع بشه\n\n"
        "موضوعاتی که می‌تونم کمک کنم:\n"
        "✅ سوال و جواب\n"
        "✅ ترجمه متن\n"
        "✅ نوشتن و ویرایش\n"
        "✅ کدنویسی\n"
        "✅ تحلیل و بررسی\n"
    )

async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("✅ مکالمه جدید شروع شد! بفرما چی می‌خوای بپرسی؟")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # نشون دادن حالت تایپ
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    reply = ask_ai(user_id, user_message)
    await update.message.reply_text(reply)


# ─── اجرا ──────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new", new_chat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ ParsMind Bot روشن شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
