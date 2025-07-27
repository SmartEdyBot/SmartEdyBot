import os
import stripe
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import openai
from stripe_checkout import checkout_39, checkout_49, checkout_59
from pdf_generator import generate_pdf
from telegram import InputFile
# 🔑 Ключи из .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

# 🌐 Поддержка языков
LANGUAGES = {
    'ru': {
        'greeting': "Привет, {name}! Я — SmartEdyBot, твой помощник.",
        'support': "Если тебе нравится моя работа, ты можешь поддержать меня:",
        'error': "❌ Не удалось создать платёжную сессию. Попробуйте позже.",
        'pay_text': "Перейдите по ссылке для оплаты: {url}"
    },
    'en': {
        'greeting': "Hello, {name}! I’m SmartEdyBot, your assistant.",
        'support': "If you like my work, you can support me:",
        'error': "❌ Failed to create a payment session. Try again later.",
        'pay_text': "Click the link to pay: {url}"
    },
    'de': {
        'greeting': "Hallo, {name}! Ich bin SmartEdyBot, dein Assistent.",
        'support': "Wenn dir meine Arbeit gefällt, kannst du mich unterstützen:",
        'error': "❌ Zahlungssitzung konnte nicht erstellt werden. Bitte später versuchen.",
        'pay_text': "Zahlungslink: {url}"
    },
    'es': {
        'greeting': "Hola, {name}! Soy SmartEdyBot, tu asistente.",
        'support': "Si te gusta mi trabajo, puedes apoyarme:",
        'error': "❌ No se pudo crear sesión de pago. Intenta más tarde.",
        'pay_text': "Enlace de pago: {url}"
    },
    'ar': {
        'greeting': "مرحبًا، {name}! أنا SmartEdyBot، مساعدك الشخصي.",
        'support': "إذا أعجبتك خدمتي، يمكنك دعمي:",
        'error': "❌ فشل في إنشاء جلسة الدفع. حاول لاحقًا.",
        'pay_text': "اضغط على الرابط للدفع: {url}"
    }
}


def get_user_language(user):
    lang = user.language_code if user.language_code else 'en'
    return LANGUAGES.get(lang, LANGUAGES['en'])

# 🟢 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_language(user)
    await update.message.reply_html(
        lang['greeting'].format(name=user.first_name)
    )
    await update.message.reply_text(
        lang['support'],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Поддержать (39€)", callback_data="checkout_39")],
            [InlineKeyboardButton("💳 Поддержать (49€)", callback_data="checkout_49")],
            [InlineKeyboardButton("💳 Поддержать (59€)", callback_data="checkout_59")],
        ])
    )

# 💳 Обработка оплаты Stripe
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_user_language(query.from_user)

    if query.data == "checkout_39":
        checkout_url = checkout_39()
    elif query.data == "checkout_49":
        checkout_url = checkout_49()
    elif query.data == "checkout_59":
        checkout_url = checkout_59()
    else:
        checkout_url = None

    if checkout_url:
        await query.edit_message_text(
            text=lang['pay_text'].format(url=checkout_url)
        )
    else:
        await query.edit_message_text(
            text=lang['error']
        )
        # ✅ Генерация PDF и отправка
        price_in_cents = int(query.data.split('_')[1]) * 100
        file_path = f"document_{query.from_user.id}.pdf"
        generate_pdf(file_path, lang, price_in_cents / 100)
        await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(file_path))
# 🤖 Ответ на обычные сообщения (GPT)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_input}]
        )
        bot_response = response.choices[0].message.content.strip()
    except Exception as e:
        bot_response = f"Произошла ошибка: {str(e)}"

    await update.message.reply_text(bot_response)

# 🚀 Запуск бота
app = ApplicationBuilder().token(TG_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()