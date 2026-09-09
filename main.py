import os
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
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
BOT_TOKEN = "8210193780:AAHgexSciAcNOhUnJkOhVxdj4Y5Mi576g-c"
ADMIN_ID = 5899402664
LOG_CHANNEL_ID = -1004483673752  # আপনার ১৩ সংখ্যার সঠিক Channel ID-টি এখানে চেক করে বসিয়ে নিন
SUPPORT_USERNAME = "ziaulx"
COIN_TRANSFER_USERNAME = "@ziaulx90"

# Disabled Coins Config
DISABLED_COINS = {
    "Niva Coin": "⚠️ **আন্তরিকভাবে দুঃখিত!**\nNiva Coin সেল সাময়িকভাবে বন্ধ আছে। দয়া করে কিছুক্ষণ পর চেষ্টা করুন।",
    "Ns Coin": "⚠️ **আন্তরিকভাবে দুঃখিত!**\nNs Coin এর স্টক ফুল হয়ে গেছে। খুব শীঘ্রই আবার চালু করা হবে।"
}

# Coin rates per 1000 (1K) coins
COIN_RATES_PER_1K = {
    "Niva Coin": 4.80,
    "Top Coin": 4.50,
    "Ns Coin": 9.80,
    "New Top": 5.50
}

# User Orders History Database
user_orders = {}
order_counter = 1000

# Conversation States
COIN_AMOUNT, NIVA_USERNAME, PAYMENT_METHOD, ACCOUNT_NO = range(4)

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
        [KeyboardButton(f"🪙 Niva Coin (1000=৳{COIN_RATES_PER_1K['Niva Coin']})"), KeyboardButton(f"🪙 Top Coin (1000=৳{COIN_RATES_PER_1K['Top Coin']})")],
        [KeyboardButton(f"🪙 Ns Coin (1000=৳{COIN_RATES_PER_1K['Ns Coin']})"), KeyboardButton(f"🪙 New Top (1000=৳{COIN_RATES_PER_1K['New Top']})")],
        [KeyboardButton("🔗 রেফারেল লিংক"), KeyboardButton("💳 Withdraw")],
        [KeyboardButton("💬 Support")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "refresh / start bot")
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"🙋‍♂️ **স্বাগতম {user.first_name}!**\n\n"
        f"কেন কাজ করবেন এই বটে?\n"
        f"✅ সবচেয়ে বেশি রেট\n"
        f"✅ দ্রুত পেমেন্ট\n"
        f"✅ বাংলাদেশি পেমেন্ট মেথড (bKash/Nagad)\n"
        f"⚠️ **সর্বনিম্ন উইথড্র limit: ৳২০**\n\n"
        f"👇 **নিচের তালিকা থেকে আপনার কয়েন সিলেক্ট করুন:**"
    )
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode='Markdown')
    return ConversationHandler.END

async def handle_coin_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
        
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "💬 Support":
        support_msg = (
            f"📞 **অ্যাডমিন সাপোর্ট / হেল্প ডেস্ক**\n\n"
            f"আপনার যেকোনো সমস্যা, পেমেন্ট সংক্রান্ত প্রশ্ন বা সহায়তার জন্য সরাসরি আমাদের সাথে যোগাযোগ করুন:\n\n"
            f"👤 **অ্যাডমিন:** @{SUPPORT_USERNAME}\n"
            f"⏱️ **সাপোর্ট টাইম:** ২৪/৭ সার্ভিস"
        )
        await update.message.reply_text(support_msg, reply_markup=get_main_keyboard(), parse_mode='Markdown')
        return ConversationHandler.END

    elif text == "💳 Withdraw":
        orders = user_orders.get(user_id, [])
        msg = "⚠️ **সর্বনিম্ন উইথড্র পরিমাণ: ৳২০**\n\n"
        
        if not orders:
            msg += "📄 **আপনার কোনো উইথড্র বা সেল অর্ডার হিস্ট্রি নেই।**"
        else:
            msg += "📑 **আপনার অর্ডারের বিবরণী ও স্ট্যাটাস:**\n\n"
            for idx, ord_data in enumerate(orders[::-1], 1):
                status_icon = "⏳ Pending"
                if ord_data['status'] == "Approved":
                    status_icon = "✅ Approved"
                elif ord_data['status'] == "Rejected":
                    status_icon = "❌ Rejected"
                    
                msg += (
                    f"**অর্ডার #{ord_data['id']}**\n"
                    f"• কয়েন: {ord_data['coin']}\n"
                    f"• পরিমাণ: {ord_data['amount']} টি\n"
                    f"• মোট টাকা: ৳{ord_data['total']}\n"
                    f"• মেথড: {ord_data['method']}\n"
                    f"• স্ট্যাটাস: **{status_icon}**\n"
                    f"---------------------------\n"
                )
        await update.message.reply_text(msg, reply_markup=get_main_keyboard(), parse_mode='Markdown')
        return ConversationHandler.END
        
    elif text == "🔗 রেফারেল লিংক":
        bot_user = (await context.bot.get_me()).username
        ref_msg = (
            f"🔗 **আপনার রেফারেল লিংক:**\n"
            f"https://t.me/{bot_user}?start={user_id}\n\n"
            f"আপনার লিংকে নতুন ইউজার যোগ দিলে পাবেন আকর্ষণীয় কমিশন!"
        )
        await update.message.reply_text(ref_msg, reply_markup=get_main_keyboard(), parse_mode='Markdown')
        return ConversationHandler.END

    selected_coin = None
    for coin in COIN_RATES_PER_1K:
        if coin in text:
            selected_coin = coin
            break
            
    if selected_coin:
        if selected_coin in DISABLED_COINS:
            await update.message.reply_text(
                DISABLED_COINS[selected_coin],
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )
            return ConversationHandler.END

        context.user_data['coin'] = selected_coin
        cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ বাতিল")]], resize_keyboard=True)
        
        await update.message.reply_text(
            f"আপনি **{selected_coin}** সিলেক্ট করেছেন।\n"
            f"প্রতি ১০০০ (1K) কয়েন রেট: **৳{COIN_RATES_PER_1K[selected_coin]}**\n\n"
            f"📥 **কত কয়েন বিক্রি করতে চান তা সংখ্যায় লিখুন (যেমন: 4000):**",
            reply_markup=cancel_keyboard,
            parse_mode='Markdown'
        )
        return COIN_AMOUNT
    else:
        await update.message.reply_text("দয়া করে নিচের মেনু থেকে যেকোনো একটি অপশন বেছে নিন।", reply_markup=get_main_keyboard())
        return ConversationHandler.END

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return COIN_AMOUNT
    text = update.message.text
    
    if text == "❌ বাতিল":
        await update.message.reply_text("❌ প্রসেসটি বাতিল করা হয়েছে।", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    try:
        amt = float(text)
        if amt <= 0:
            await update.message.reply_text("⚠️ পরিমাণ অবশ্যই ০ এর বেশি হতে হবে। সঠিক সংখ্যা লিখুন:")
            return COIN_AMOUNT
            
        coin = context.user_data['coin']
        rate_per_1k = COIN_RATES_PER_1K[coin]
        total = round((amt / 1000.0) * rate_per_1k, 2)
        
        context.user_data['amt'] = amt
        context.user_data['total'] = total
        
        cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ বাতিল")]], resize_keyboard=True)
        
        username_prompt = (
            f"📤 **কয়েন ট্রান্সফার করার জন্য নিচের আইডিতে সেন্ড করুন:**\n\n"
            f"👤 **Target Username / ID:** `{COIN_TRANSFER_USERNAME}`\n\n"
            f"🔗 ওপরের ইউজারনেমটি কপি করে কয়েন সেন্ড করুন এবং আপনার অ্যাকাউন্ট/ইউজারনেমটি এখানে লিখে পাঠান:"
        )
        await update.message.reply_text(username_prompt, reply_markup=cancel_keyboard, parse_mode='Markdown')
        return NIVA_USERNAME
        
    except ValueError:
        await update.message.reply_text("⚠️ ভুল ইনপুট! দয়া করে শুধু সংখ্যা লিখুন (যেমন: 4000):")
        return COIN_AMOUNT

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return NIVA_USERNAME
    text = update.message.text
    
    if text == "❌ বাতিল":
        await update.message.reply_text("❌ প্রসেসটি বাতিল করা হয়েছে।", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    context.user_data['sender_account'] = text
    
    amt = context.user_data.get('amt')
    total = context.user_data.get('total')
    coin = context.user_data.get('coin')
    
    warning = ""
    if total < 20.0:
        warning = "\n⚠️ **সতর্কতা:** সর্বনিম্ন উইথড্র পরিমাণ ২০ টাকা! এই অর্ডারের মোট টাকা ৳২০ এর কম।"
        
    payment_keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("bKash"), KeyboardButton("Nagad")],
        [KeyboardButton("❌ বাতিল")]
    ], resize_keyboard=True)
    
    await update.message.reply_text(
        f"📊 **অর্ডার সারসংক্ষেপ:**\n"
        f"• কয়েন: {coin}\n"
        f"• পরিমাণ: {amt} টি\n"
        f"• মোট পাবেন: **৳{total}**{warning}\n\n"
        f"👇 **আপনার পেমেন্ট মেথড সিলেক্ট করুন:**",
        reply_markup=payment_keyboard,
        parse_mode='Markdown'
    )
    return PAYMENT_METHOD

async def select_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return PAYMENT_METHOD
    text = update.message.text
    
    if text == "❌ বাতিল":
        await update.message.reply_text("❌ প্রসেসটি বাতিল করা হয়েছে।", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    if text in ["bKash", "Nagad"]:
        context.user_data['method'] = text
        cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ বাতিল")]], resize_keyboard=True)
        
        await update.message.reply_text(
            f"📲 **{text} অ্যাকাউন্ট তথ্য:**\n"
            f"আপনার {text} নম্বর এবং পেমেন্ট রিসিভ করার ডিটেইলস লিখে জানান:",
            reply_markup=cancel_keyboard
        )
        return ACCOUNT_NO
    else:
        await update.message.reply_text("দয়া করে bKash অথবা Nagad সিলেক্ট করুন:")
        return PAYMENT_METHOD

async def save_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global order_counter
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text
    
    if text == "❌ বাতিল":
        await update.message.reply_text("❌ প্রসেসটি বাতিল করা হয়েছে।", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    u = update.effective_user
    info = text
    c = context.user_data.get('coin')
    amt = context.user_data.get('amt')
    tot = context.user_data.get('total')
    m = context.user_data.get('method')
    sender_acc = context.user_data.get('sender_account')
    
    order_id = order_counter
    order_counter += 1

    order_item = {
        'id': order_id,
        'coin': c,
        'amount': amt,
        'total': tot,
        'method': m,
        'status': 'Pending'
    }
    if u.id not in user_orders:
        user_orders[u.id] = []
    user_orders[u.id].append(order_item)

    await update.message.reply_text(
        f"✅ **আপনার অর্ডারটি সফলভাবে জমা হয়েছে! (Order #{order_id})**\n"
        f"স্ট্যাটাস: **⏳ Pending**\n"
        f"আপনি **💳 Withdraw** অপশনে ক্লিক করে যেকোনো সময় অর্ডারের বিবরণ ও স্ট্যাটাস দেখতে পারবেন।",
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )
    
    admin_msg = (
        f"📥 **নতুন সেল অর্ডার! (#Order_{order_id})**\n\n"
        f"👤 ইউজার: {u.first_name} (`{u.id}`)\n"
        f"🪙 কয়েন: **{c}**\n"
        f"🔢 পরিমাণ: **{amt}**\n"
        f"💰 মোট টাকা: **৳{tot}**\n"
        f"📤 সেন্ডারের অ্যাকাউন্ট/আইডি: `{sender_acc}`\n"
        f"💳 মেথড: **{m}**\n"
        f"📝 পেমেন্ট নম্বর/ডিটেইলস: `{info}`"
    )
    
    admin_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"app_{u.id}_{order_id}_{tot}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{u.id}_{order_id}")
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
        _, user_id, order_id, amount = data.split("_")
        user_id = int(user_id)
        order_id = int(order_id)
        
        if user_id in user_orders:
            for item in user_orders[user_id]:
                if item['id'] == order_id:
                    item['status'] = "Approved"

        new_text = query.message.text + f"\n\n✅ **অনুমোদিত হয়েছে** (By {admin_user})"
        await query.edit_message_text(text=new_text)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 **আপনার Order #{order_id} সফলভাবে অনুমোদিত হয়েছে!**\nআপনার অ্যাকাউন্টে ৳{amount} পেমেন্ট করে দেওয়া হয়েছে।"
            )
        except Exception:
            pass
            
    elif data.startswith("rej_"):
        _, user_id, order_id = data.split("_")
        user_id = int(user_id)
        order_id = int(order_id)
        
        if user_id in user_orders:
            for item in user_orders[user_id]:
                if item['id'] == order_id:
                    item['status'] = "Rejected"

        new_text = query.message.text + f"\n\n❌ **বাতিল করা হয়েছে** (By {admin_user})"
        await query.edit_message_text(text=new_text)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ **আপনার Order #{order_id} বাতিল করা হয়েছে।**\nসঠিক তথ্য প্রদান করে আবার চেষ্টা করুন।"
            )
        except Exception:
            pass

def main():
    keep_alive()
    app_bot = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^(🪙|🔗|💳|💬)'), handle_coin_selection)],
        states={
            COIN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            NIVA_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_payment)],
            ACCOUNT_NO: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_order)],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex('^❌ বাতিল$'), start)
        ]
    )

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(conv)
    app_bot.add_handler(CallbackQueryHandler(handle_admin_action, pattern=r'^(app_|rej_)'))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_coin_selection))
    
    app_bot.run_polling()

if __name__ == '__main__':
    main()
