import os
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# Configurations
BOT_TOKEN = "8210193780:AAG3-gzVcqY7PHAHXT56J1HSBEm2ju6xQk0"
ADMIN_ID = 5899402664
LOG_CHANNEL_ID = -1003948006284

# Coin rates
COIN_RATES = {
    "Niva Coin": 4.20,
    "Top Coin": 4.50,
    "Ns Coin": 9.20,
    "New Top": 5.50
}

COIN_AMOUNT, PAYMENT_METHOD, ACCOUNT_NO = range(3)

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

def get_main_keyboard():
    keyboard = [
        [KeyboardButton(f"🪙 Niva Coin (৳{COIN_RATES['Niva Coin']})"), KeyboardButton(f"🪙 Top Coin (৳{COIN_RATES['Top Coin']})")],
        [KeyboardButton(f"🪙 Ns Coin (৳{COIN_RATES['Ns Coin']})"), KeyboardButton(f"🪙 New Top (৳{COIN_RATES['New Top']})")],
        [KeyboardButton("🔗 রেফারেল লিংক"), KeyboardButton("🛡️ পেমেন্ট প্রুফ")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"🙋‍♂️ **স্বাগতম {user.first_name}!**\n\n"
        f"কেন কাজ করবেন এই বটে?\n"
        f"✅ সবচেয়ে বেশি রেট\n"
        f"✅ দ্রুত পেমেন্ট\n"
        f"✅ বাংলাদেশি পেমেন্ট মেথড (bKash/Nagad)\n\n"
        f"👇 **নিচের তালিকা থেকে আপনার কয়েন সিলেক্ট করুন:**"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode='Markdown')
    return ConversationHandler.END

async def handle_coin_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    selected_coin = None
    for coin in COIN_RATES:
        if coin in text:
            selected_coin = coin
            break
            
    if selected_coin:
        context.user_data['coin'] = selected_coin
        cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ বাতিল")]], resize_keyboard=True)
        
        await update.message.reply_text(
            f"আপনি **{selected_coin}** সিলেক্ট করেছেন।\n"
            f"প্রতি কয়েন রেট: **৳{COIN_RATES[selected_coin]}**\n\n"
            f"📥 **কত কয়েন বিক্রি করতে চান তা সংখ্যায় লিখুন:**",
            reply_markup=cancel_keyboard,
            parse_mode='Markdown'
        )
        return COIN_AMOUNT
    
    elif text == "🔗 রেফারেল লিংক":
        bot_user = (await context.bot.get_me()).username
        ref_msg = (
            f"🔗 **আপনার রেফারেল লিংক:**\n"
            f"https://t.me/{bot_user}?start={update.effective_user.id}\n\n"
            f"আপনার লিংকে নতুন ইউজার যোগ দিলে পাবেন আকর্ষণীয় কমিশন!"
        )
        await update.message.reply_text(ref_msg, reply_markup=get_main_keyboard(), parse_mode='Markdown')
        return ConversationHandler.END
        
    elif text == "🛡️ পেমেন্ট প্রুফ":
        await update.message.reply_text("🛡️ পেমেন্ট প্রুফ দেখতে আমাদের চ্যানেলে যুক্ত থাকুন:\nhttps://t.me/your_proof_channel", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    else:
        await update.message.reply_text("দয়া করে নিচের মেনু থেকে যেকোনো একটি অপশন বেছে নিন।", reply_markup=get_main_keyboard())
        return ConversationHandler.END

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "❌ বাতিল":
        await update.message.reply_text("❌ প্রসেসটি বাতিল করা হয়েছে।", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    try:
        amt = float(text)
        if amt <= 0:
            await update.message.reply_text("⚠️ পরিমাণ অবশ্যই ০ এর বেশি হতে হবে। সঠিক সংখ্যা লিখুন:")
            return COIN_AMOUNT
            
        coin = context.user_data['coin']
        total = round(amt * COIN_RATES[coin], 2)
        context.user_data['amt'] = amt
        context.user_data['total'] = total
        
        payment_keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("bKash"), KeyboardButton("Nagad")],
            [KeyboardButton("❌ বাতিল")]
        ], resize_keyboard=True)
        
        await update.message.reply_text(
            f"📊 **অর্ডার সারসংক্ষেপ:**\n"
            f"• কয়েন: {coin}\n"
            f"• পরিমাণ: {amt}\n"
            f"• মোট পাবেন: **৳{total}**\n\n"
            f"👇 **আপনার পেমেন্ট মেথড সিলেক্ট করুন:**",
            reply_markup=payment_keyboard,
            parse_mode='Markdown'
        )
        return PAYMENT_METHOD
    except ValueError:
        await update.message.reply_text("⚠️ ভুল ইনপুট! দয়া করে শুধু সংখ্যা লিখুন (যেমন: 100):")
        return COIN_AMOUNT

async def select_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "❌ বাতিল":
        await update.message.reply_text("❌ প্রসেসটি বাতিল করা হয়েছে।", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    if text in ["bKash", "Nagad"]:
        context.user_data['method'] = text
        cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ বাতিল")]], resize_keyboard=True)
        
        await update.message.reply_text(
            f"📲 **{text} অ্যাকাউন্ট তথ্য:**\n"
            f"আপনার {text} নম্বর এবং কয়েন পাঠানোর প্রুফ/ট্রানজেকশন আইডি লিখে পাঠ জানান:",
            reply_markup=cancel_keyboard
        )
        return ACCOUNT_NO
    else:
        await update.message.reply_text("দয়া করে bKash অথবা Nagad সিলেক্ট করুন:")
        return PAYMENT_METHOD

async def save_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "❌ বাতিল":
        await update.message.reply_text("❌ প্রসেসটি বাতিল করা হয়েছে।", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    u = update.effective_user
    info = text
    c = context.user_data.get('coin')
    amt = context.user_data.get('amt')
    tot = context.user_data.get('total')
    m = context.user_data.get('method')

    await update.message.reply_text(
        "✅ **আপনার অর্ডারটি সফলভাবে জমা হয়েছে!**\n"
        "খুব শীঘ্রই আপনার পেমেন্ট কমপ্লিট করা হবে। ধন্যবাদ!",
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )
    
    admin_msg = (
        f"📥 **নতুন সেল অর্ডার!**\n\n"
        f"👤 ইউজার: [{u.first_name}](tg://user?id={u.id}) (`{u.id}`)\n"
        f"🪙 কয়েন: **{c}**\n"
        f"🔢 পরিমাণ: **{amt}**\n"
        f"💰 মোট টাকা: **৳{tot}**\n"
        f"💳 মেথড: **{m}**\n"
        f"📝 ডিটেইলস: `{info}`"
    )
    
    admin_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"app_{u.id}_{tot}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{u.id}")
        ]
    ])

    try:
        await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=admin_msg, reply_markup=admin_buttons, parse_mode='Markdown')
    except Exception as e:
        print(f"Error sending log: {e}")
        
    return ConversationHandler.END

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    admin_user = query.from_user.first_name
    
    if data.startswith("app_"):
        _, user_id, amount = data.split("_")
        new_text = query.message.text + f"\n\n✅ **অনুমোদিত হয়েছে** (By {admin_user})"
        await query.edit_message_text(text=new_text)
        
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"🎉 **আপনার অর্ডারটি সফলভাবে অনুমোদিত হয়েছে!**\nআপনার অ্যাকাউন্টে ৳{amount} পেমেন্ট করা হয়েছে।"
            )
        except Exception:
            pass
            
    elif data.startswith("rej_"):
        _, user_id = data.split("_")
        new_text = query.message.text + f"\n\n❌ **বাতিল করা হয়েছে** (By {admin_user})"
        await query.edit_message_text(text=new_text)
        
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text="❌ **আপনার অর্ডারটি বাতিল করা হয়েছে।**\nসঠিক তথ্য প্রদান করে আবার চেষ্টা করুন অথবা অ্যাডমিনের সাথে যোগাযোগ করুন।"
            )
        except Exception:
            pass

def main():
    keep_alive()
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^(🪙|🔗|🛡️)'), handle_coin_selection)],
        states={
            COIN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_payment)],
            ACCOUNT_NO: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_order)],
        },
        fallbacks=[MessageHandler(filters.Regex('^❌ বাতিল$'), start)]
    )

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(conv)
    app_bot.add_handler(CallbackQueryHandler(handle_admin_action, pattern=r'^(app_|rej_)'))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_coin_selection))
    
    app_bot.run_polling()

if __name__ == '__main__':
    main()
