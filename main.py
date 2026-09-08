import os
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# Configurations
BOT_TOKEN = "8210193780:AAG3-gzVcqY7PHAHXT56J1HSBEm2ju6xQk0"
ADMIN_ID = 5899402664
REFERRAL_PERCENT = 3.0

COIN_RATES = {
    "Niva Coin": 4.50,
    "Top Coin": 4.10,
    "Ns Coin": 10.0
}

COIN_CHOICE, COIN_AMOUNT, PAYMENT_METHOD, ACCOUNT_NO = range(4)

# Web server setup
app = Flask('')

@app.route('/')
def home():
    return "Bot status: Running"

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    if args and args[0].isdigit():
        ref = int(args[0])
        if ref != user.id:
            context.user_data['referrer'] = ref

    keyboard = [
        [InlineKeyboardButton("💰 Today's Rates", callback_data='rates')],
        [InlineKeyboardButton("📤 Sell Coin", callback_data='sell')],
        [InlineKeyboardButton("🔗 Referral Link", callback_data='ref')],
        [InlineKeyboardButton("🛡️ Payment Proof", url='https://t.me/your_proof_channel')]
    ]
    await update.message.reply_text(f"হ্যালো {user.first_name}! Niva Coin Buy-Sell বটে স্বাগতম।", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'rates':
        msg = "📊 **আজকের কয়েন রেট:**\n\n"
        for coin, rate in COIN_RATES.items():
            msg += f"• {coin}: {rate} ৳\n"
        await query.edit_message_text(msg, parse_mode='Markdown')
    elif query.data == 'ref':
        bot_user = (await context.bot.get_me()).username
        msg = f"🔗 **আপনার রেফারেল লিংক:**\nhttps://t.me/{bot_user}?start={query.from_user.id}\n\nকমিশন: **{REFERRAL_PERCENT}%**"
        await query.edit_message_text(msg, parse_mode='Markdown')

async def start_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(c, callback_data=f'c_{c}')] for c in COIN_RATES]
    await query.edit_message_text("কোন কয়েন বিক্রি করবেন সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard))
    return COIN_CHOICE

async def select_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coin = query.data.replace('c_', '')
    context.user_data['coin'] = coin
    await query.edit_message_text(f"**{coin}** এর পরিমাণ (সংখ্যায়) লিখুন:")
    return COIN_AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amt = float(update.message.text)
        coin = context.user_data['coin']
        total = amt * COIN_RATES[coin]
        context.user_data['amt'] = amt
        context.user_data['total'] = total
        keyboard = [[InlineKeyboardButton("bKash", callback_data='p_bKash'), InlineKeyboardButton("Nagad", callback_data='p_Nagad')]]
        await update.message.reply_text(f"মোট: **{total} ৳**\nপেমেন্ট মেথড সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return PAYMENT_METHOD
    except ValueError:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন:")
        return COIN_AMOUNT

async def select_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['method'] = query.data.replace('p_', '')
    await query.edit_message_text("আপনার নম্বর ও প্রুফ ইনফো লিখে পাঠান:")
    return ACCOUNT_NO

async def save_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    info = update.message.text
    c = context.user_data.get('coin')
    amt = context.user_data.get('amt')
    tot = context.user_data.get('total')
    m = context.user_data.get('method')

    await update.message.reply_text("✅ অর্ডারটি সফলভাবে জমা হয়েছে!")
    
    admin_msg = f"📥 **নতুন অর্ডার!**\n• User ID: `{u.id}`\n• Coin: {c}\n• Amount: {amt}\n• Total: {tot} BDT\n• Method: {m}\n• Info: {info}"
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode='Markdown')
    except Exception:
        pass
    return ConversationHandler.END

async def set_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        c_name = " ".join(context.args[:-1])
        val = float(context.args[-1])
        for k in COIN_RATES:
            if k.lower() == c_name.lower():
                COIN_RATES[k] = val
                await update.message.reply_text(f"✅ {k}-এর রেট: {val} ৳")
                return
        await update.message.reply_text("❌ সঠিক কয়েনের নাম লিখুন।")
    except Exception:
        await update.message.reply_text("ফরম্যাট: `/setrate Niva Coin 4.80`", parse_mode='Markdown')

def main():
    keep_alive()
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_sell, pattern='^sell$')],
        states={
            COIN_CHOICE: [CallbackQueryHandler(select_coin, pattern='^c_')],
            COIN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            PAYMENT_METHOD: [CallbackQueryHandler(select_payment, pattern='^p_')],
            ACCOUNT_NO: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_order)],
        },
        fallbacks=[]
    )

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("setrate", set_rate))
    app_bot.add_handler(conv)
    app_bot.add_handler(CallbackQueryHandler(button_click))
    
    app_bot.run_polling()

if __name__ == '__main__':
    main()
