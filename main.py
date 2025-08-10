# === SmartEdyBot / main.py ===
# Совместимо с: python-telegram-bot==21.7, openai==1.x, flask==3.x, stripe==8.x, python-dotenv==1.1.1, fpdf2==2.7.10

import os
import sys
from threading import Thread

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from flask import Flask

# Stripe/оплата и PDF (модули из твоего проекта)
from stripe_checkout import checkout_39, checkout_49, checkout_59
from pdf_generator import generate_pdf

# OpenAI SDK v1.x
from openai import OpenAI


# ---------- ENV ----------
load_dotenv()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")  # на будущее, сейчас берётся в stripe_checkout.py

if not TG_BOT_TOKEN:
    raise RuntimeError("TG_BOT_TOKEN is not set")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

# OpenAI клиент
ai = OpenAI(api_key=OPENAI_API_KEY)


# ---------- Языки ----------
LANGUAGES = {
    "ru": {
        "greeting": "Привет, {name}! Я — SmartEdyBot, твой помощник.",
        "support": "Если тебе нравится моя работа, ты можешь поддержать меня:",
        "error": "❌ Не удалось создать платёжную сессию. Попробуйте позже.",
        "pay_text": "Перейдите по ссылке для оплаты: {url}",
        "pdf_ready": "Ваш документ готов, отправляю PDF.",
    },
    "en": {
        "greeting": "Hello, {name}! I'm SmartEdyBot, your assistant.",
        "support": "If you like my work, you can support me:",
        "error": "❌ Failed to create a payment session. Try again later.",
        "pay_text": "Click the link to pay: {url}",
        "pdf_ready": "Your document is ready. Sending PDF.",
    },
    "de": {
        "greeting": "Hallo, {name}! Ich bin SmartEdyBot, dein Assistent.",
        "support": "Wenn dir meine Arbeit gefällt, kannst du mich unterstützen:",
        "error": "❌ Zahlungssitzung konnte nicht erstellt werden. Bitte später versuchen.",
        "pay_text": "Zum Bezahlen auf den Link klicken: {url}",
        "pdf_ready": "Ihr Dokument ist fertig. Sende die PDF-Datei.",
    },
    "es": {
        "greeting": "Hola, {name}! Soy SmartEdyBot, tu asistente.",
        "support": "Si te gusta mi trabajo, puedes apoyarme:",
        "error": "❌ No se pudo crear sesión de pago. Intenta más tarde.",
        "pay_text": "Enlace de pago: {url}",
        "pdf_ready": "Tu documento está listo. Enviando PDF.",
    },
    "ar": {
        "greeting": "مرحبًا، {name}! أنا SmartEdyBot مساعدك.",
        "support": "إذا أعجبك عملي يمكنك دعمي:",
        "error": "❌ فشل إنشاء جلسة الدفع. حاول لاحقًا.",
        "pay_text": "رابط الدفع: {url}",
        "pdf_ready": "ملفّك جاهز. سأرسل PDF الآن.",
    },
}


def get_user_language(user) -> str:
    code = getattr(user, "language_code", None) or "en"
    return LANGUAGES.get(code, LANGUAGES["en"])


# ---------- Хэндлеры ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    lang = get_user_language(user)

    kb = [
        [
            InlineKeyboardButton("Поддержать (39€)", callback_data="checkout_39"),
            InlineKeyboardButton("Поддержать (49€)", callback_data="checkout_49"),
            InlineKeyboardButton("Поддержать (59€)", callback_data="checkout_59"),
        ]
    ]
    await update.message.reply_html(
        lang["greeting"].format(name=user.first_name)
    )
    await update.message.reply_text(
        lang["support"],
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Кнопки оплаты → создаём Stripe checkout ссылку,
    отправляем ссылку; (дополнительно оставляем тестовую генерацию PDF)."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    lang = get_user_language(user)

    data = query.data
    if data == "checkout_39":
        checkout_url = checkout_39()
        price_eur = 39
    elif data == "checkout_49":
        checkout_url = checkout_49()
        price_eur = 49
    elif data == "checkout_59":
        checkout_url = checkout_59()
        price_eur = 59
    else:
        checkout_url = None
        price_eur = 0

    if checkout_url:
        # 1) Ссылка на оплату
        await query.edit_message_text(lang["pay_text"].format(url=checkout_url))
        # 2) Тестовая генерация PDF (как в твоей версии)
        try:
            # путь к временному PDF
            pdf_path = f"document_from_{user.id}.pdf"
            # твоя функция generate_pdf может принимать (path, language, price_eur)
            # или (language, price_eur). Подставь подходящий вариант:
            try:
                # вариант как у тебя в старом коде
                generate_pdf(pdf_path, language=user.language_code or "en", price_eur=price_eur)
            except TypeError:
                # запасной вариант (если сигнатура другая)
                generate_pdf(language=user.language_code or "en", price_eur=price_eur, pdf_path=pdf_path)

            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=InputFile(pdf_path),
                caption=lang["pdf_ready"],
            )
        except Exception as e:
            # Лог, но не падаем
            print(f"PDF error: {e}")
        finally:
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except Exception:
                pass
    else:
        await query.edit_message_text(lang["error"])


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ответ на обычные сообщения через OpenAI."""
    text = update.message.text or ""
    try:
        resp = ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты дружелюбный помощник SmartEdyBot."},
                {"role": "user", "content": text},
            ],
            temperature=0.4,
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Произошла ошибка: {e}"

    await update.message.reply_text(answer)


# ---------- Мини‑веб для Render (держим открытый порт) ----------
_web = Flask(__name__)

@_web.get("/")
def _ping():
    return "OK", 200


def _run_web():
    # Render прокидывает PORT в env
    port = int(os.environ.get("PORT", "10000"))
    _web.run(host="0.0.0.0", port=port)


# ---------- Запуск бота ----------
def main() -> None:
    # запускаем мини‑веб в отдельном потоке
    Thread(target=_run_web, daemon=True).start()

    application = ApplicationBuilder().token(TG_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling(stop_signals=None)


if __name__ == "__main__":
    main()

