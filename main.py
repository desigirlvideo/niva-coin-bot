import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configurations
BOT_TOKEN = "8210193780:AAG3-gzVcqY7PHAHXT56J1HSBEm2ju6xQk0"
ADMIN_ID = 5899402664
REFERRAL_PERCENT = 3.0  # ৩% কমিশন

# Default Coin Rates (BDT per coin)
COIN_RATES = {
    "Niva Coin": 4.50,
    "Top Coin": 4.10,
    "Ns Coin": 10.0
}

# Flask Server for Keep-Alive
app = Flask('')

@app.route('/')
def home():
    return "Niva Coin Bot is Live and Running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    
    # Track Referral
    if args and args[0].isdigit():
        referrer_id = int(args[0])
        if referrer_id != user.id:
            context.user_data['referrer'] = referrer_id

    keyboard = [
        [InlineKeyboardButton("💰 Today's Rates", callback_data='rates')],
        [InlineKeyboardButton("🔗 Referral Link", callback_data='ref')],
        [InlineKeyboardButton("🛡️ Payment Proof", url='https://t.me/your_proof_channel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"হ্যালো {user.first_name}! Niva Coin Buy-Sell বটে আপনাকে স্বাগতম।", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'rates':
        rate_msg = "📊 **আজকের কয়েন রেট:**\n\n"
        for coin, rate in COIN_RATES.items():
            rate_msg += f"• {coin}: {rate} ৳\n"
        await query.edit_message_text(rate_msg, parse_mode='Markdown')
        
    elif query.data == 'ref':
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={query.from_user.id}"
        msg = f"🔗 **আপনার রেফারেল লিংক:**\n`{ref_link}`\n\nবন্ধুদের রেফার করলে তাদের প্রতিটি বিক্রয়ে পেয়ে যাবেন **{REFERRAL_PERCENT}%** কমিশন!"
        await query.edit_message_text(msg, parse_mode='Markdown')

async def set_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        coin_name = context.args[0]
        new_rate = float(context.args[1])
        if coin_name in COIN_RATES:
            COIN_RATES[coin_name] = new_rate
            await update.message.reply_text(f"✅ {coin_name}-এর নতুন দাম সেট করা হয়েছে: {new_rate} ৳")
        else:
            await update.message.reply_text("❌ সঠিক কয়েনের নাম লিখুন। (Niva Coin / Top Coin / Ns Coin)")
    except IndexError:
        await update.message.reply_text("ফরম্যাট: `/setrate Niva Coin 4.80`", parse_mode='Markdown')

def main():
    keep_alive()
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setrate", set_rate))
    application.add_handler(CallbackQueryHandler(button_click))
    
    application.run_polling()

if __name__ == '__main__':
    main()
