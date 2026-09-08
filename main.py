import os
import asyncio
from threading import Thread
from flask import Flask
from openpyxl import Workbook, load_workbook
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
EXCEL_FILE = "coin_data.xlsx"
REFERRAL_PERCENT = 3.0  # ৩% কমিশন

# Default Coin Rates (BDT per coin)
COIN_RATES = {
    "Niva Coin": 4.50,
    "Top Coin": 4.10,
    "Ns Coin": 10.0
}

# Conversation States for Selling
COIN_CHOICE, COIN_AMOUNT, PAYMENT_METHOD, ACCOUNT_NO = range(4)

# Ensure Excel file exists
if not os.path.exists(EXCEL_FILE):
    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"
    ws.append(["User ID", "Username", "Coin", "Amount", "Total BDT", "Payment Method", "Account", "Status"])
    wb.save(EXCEL_FILE)

# Flask Web Server for Render Uptime
app = Flask(__name__)

@app.route('/')
def home():
    return "Niva Coin Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Bot Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    
    if args and args[0].isdigit():
        referrer_id = int(args[0])
        if referrer_id != user.id:
            context.user_data['referrer'] = referrer_id

    keyboard = [
        [InlineKeyboardButton("💰 Today's Rates", callback_data='rates')],
        [InlineKeyboardButton("📤 Sell Coin", callback_data='sell')],
        [InlineKeyboardButton("🔗 Referral Link", callback_data='ref')],
        [InlineKeyboardButton("🛡️ Payment Proof", url='https://t.me/your_proof_channel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"হ্যালো {user.first_name}! Niva Coin Buy-Sell বটে আপনাকে স্বাগতম।",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

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

# Coin Sell Flow
async def start_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Niva Coin", callback_data='coin_Niva Coin')],
        [InlineKeyboardButton("Top Coin", callback_data='coin_Top Coin')],
        [InlineKeyboardButton("Ns Coin", callback_data='coin_Ns Coin')]
    ]
    await query.edit_message_text("আপনি কোন কয়েনটি বিক্রি করতে চান?", reply_markup=InlineKeyboardMarkup(keyboard))
    return COIN_CHOICE

async def select_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    coin_selected = query.data.replace('coin_', '')
    context.user_data['selected_coin'] = coin_selected
    
    await query.edit_message_text(f"আপনি **{coin_selected}** বেছে নিয়েছেন। কতগুলো কয়েন বিক্রি করবেন তা সংখ্যায় লিখুন:")
    return COIN_AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        coin = context.user_data['selected_coin']
        rate = COIN_RATES.get(coin, 0)
        total_bdt = amount * rate
        
        context.user_data['amount'] = amount
        context.user_data['total_bdt'] = total_bdt
        
        keyboard = [
            [InlineKeyboardButton("bKash", callback_data='pay_bKash'), InlineKeyboardButton("Nagad", callback_data='pay_Nagad')]
        ]
        await update.message.reply_text(
            f"মোট টাকা: **{total_bdt} ৳**\nপেমেন্ট গ্রহণের মাধ্যম সিলেক্ট করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return PAYMENT_METHOD
    except ValueError:
        await update.message.reply_text("❌ সঠিক সংখ্যা লিখুন। (যেমন: 100)")
        return COIN_AMOUNT

async def select_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    method = query.data.replace('pay_', '')
    context.user_data['payment_method'] = method
    
    await query.edit_message_text(f"আপনার **{method}** নম্বরটি এবং কয়েন ট্রান্সফারের প্রমাণ বা আইডি টাইপ করে দিন:")
    return ACCOUNT_NO

async def save_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    account_info = update.message.text
    coin = context.user_data.get('selected_coin')
    amount = context.user_data.get('amount')
    total_bdt = context.user_data.get('total_bdt')
    method = context.user_data.get('payment_method')

    # Save to Excel
    wb = load_workbook(EXCEL_FILE)
    ws = wb["Orders"]
    ws.append([user.id, user.username or "", coin, amount, total_bdt, method, account_info, "Pending"])
    wb.save(EXCEL_FILE)

    await update.message.reply_text("✅ আপনার অর্ডারটি সফলভাবে জমা হয়েছে! অ্যাডমিন যাচাই করে দ্রুত পেমেন্ট পাঠিয়ে দেবে।")
    
    # Notify Admin
    admin_msg = (
        f"📥 **নতুন সেল অর্ডার!**\n\n"
        f"• User ID: `{user.id}`\n"
        f"• Coin: {coin}\n"
        f"• Amount: {amount}\n"
        f"• Total: {total_bdt} BDT\n"
        f"• Method: {method}\n"
        f"• Info: {account_info}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode='Markdown')
    except Exception:
        pass

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("প্রক্রিয়াটি বাতিল করা হয়েছে।")
    return ConversationHandler.END

# Admin Set Rate Command
async def set_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        coin_input = " ".join(context.args[:-1])
        new_rate = float(context.args[-1])
        
        found = False
        for coin_key in COIN_RATES:
            if coin_key.lower() == coin_input.lower():
                COIN_RATES[coin_key] = new_rate
                found = True
                await update.message.reply_text(f"✅ {coin_key}-এর নতুন রেট: {new_rate} ৳")
                break
        if not found:
            await update.message.reply_text("❌ সঠিক কয়েন নাম দিন। (Niva Coin / Top Coin / Ns Coin)")
    except (IndexError, ValueError):
        await update.message.reply_text("ফরম্যাট: `/setrate Niva Coin 4.80`", parse_mode='Markdown')

def main():
    keep_alive()
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_sell, pattern='^sell$')],
        states={
            COIN_CHOICE: [CallbackQueryHandler(select_coin, pattern='^coin_')],
            COIN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            PAYMENT_METHOD: [CallbackQueryHandler(select_payment, pattern='^pay_')],
            ACCOUNT_NO: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_order)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setrate", set_rate))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_click))
    
    application.run_polling()

if __name__ == '__main__':
    main()
