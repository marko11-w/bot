import os
import json
from flask import Flask, request
import telebot
from telebot import types

# ✅ توكن البوت (تم إدخاله يدويًا – لا تشاركه علنًا)
TOKEN = "7837218696:AAGSozPdf3hLT0bBjrgB3uExeuir-90Rvok"

# إعدادات
ADMIN_ID = 7758666677  # آيدي الأدمن
CHANNEL_USERNAME = "@MARK01i"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

FILES = {
    "settings": "settings.json",
    "banned": "banned_users.json",
    "pending": "pending_requests.json"
}

def load_json(name):
    try:
        with open(FILES[name], "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {} if name == "pending" else []

def save_json(name, data):
    with open(FILES[name], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# إعداد افتراضي إن لم يكن موجودًا
if not load_json("settings"):
    save_json("settings", {
        "bot_active": True,
        "games": ["🎮 ببجي", "🔥 فري فاير", "⚽ بيس", "🎯 أخرى"],
        "messages": {
            "start": "👋 أهلاً بك في بوت بيع وتبادل الحسابات.\nأرسل صورة الحساب لبدء العملية.",
            "must_subscribe": f"🚫 يجب الاشتراك في القناة أولًا: {CHANNEL_USERNAME}"
        }
    })

@app.route("/", methods=["GET", "POST"])
def webhook():
    if request.method == "POST":
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "ok"
    return "Bot is running."

@bot.message_handler(commands=["start"])
def start(message):
    if load_json("settings").get("bot_active", True) is False:
        return bot.reply_to(message, "🔒 البوت متوقف حالياً.")
    
    if str(message.from_user.id) in load_json("banned"):
        return bot.reply_to(message, "🚫 تم حظرك من استخدام هذا البوت.")
    
    bot.send_message(message.chat.id, load_json("settings")["messages"]["start"])
    bot.send_message(message.chat.id, "📸 أرسل صورة الحساب للبيع أو التبادل.")
    bot.register_next_step_handler(message, receive_image)

def receive_image(message):
    if not message.photo:
        return bot.reply_to(message, "📸 الرجاء إرسال صورة فقط.")
    
    user_id = str(message.from_user.id)
    pending = load_json("pending")
    pending[user_id] = {"photo": message.photo[-1].file_id}
    save_json("pending", pending)
    
    bot.send_message(message.chat.id, "📝 أرسل وصف الحساب:")
    bot.register_next_step_handler(message, receive_description)

def receive_description(message):
    user_id = str(message.from_user.id)
    pending = load_json("pending")
    if user_id not in pending:
        return
    
    pending[user_id]["description"] = message.text
    save_json("pending", pending)
    
    games = load_json("settings")["games"]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for g in games:
        markup.add(g)
    bot.send_message(message.chat.id, "🎮 اختر نوع اللعبة:", reply_markup=markup)
    bot.register_next_step_handler(message, receive_game)

def receive_game(message):
    user_id = str(message.from_user.id)
    pending = load_json("pending")
    pending[user_id]["game"] = message.text
    save_json("pending", pending)
    
    bot.send_message(message.chat.id, "💵 كم سعر الحساب؟", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, receive_price)

def receive_price(message):
    user_id = str(message.from_user.id)
    try:
        float(message.text)
        price = f"${message.text}"
    except:
        return bot.reply_to(message, "❌ يرجى إدخال رقم فقط.")
    
    pending = load_json("pending")
    pending[user_id]["price"] = price
    save_json("pending", pending)

    bot.send_message(message.chat.id, "✅ تم استلام الطلب، وسيتم مراجعته من قبل الإدارة.")
    
    data = pending[user_id]
    caption = f"📌 طلب جديد من: @{message.from_user.username or 'غير معروف'}\n\n" \
              f"🎮 اللعبة: {data['game']}\n💬 الوصف: {data['description']}\n💵 السعر: {data['price']}\n🆔 ID: {user_id}"

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")
    )
    bot.send_photo(ADMIN_ID, data["photo"], caption=caption, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_") or c.data.startswith("reject_"))
def handle_decision(call):
    action, user_id = call.data.split("_")
    pending = load_json("pending")
    if user_id not in pending:
        return bot.answer_callback_query(call.id, "❌ الطلب غير موجود.")
    
    data = pending[user_id]
    if action == "accept":
        caption = f"🎮 {data['game']}\n💬 {data['description']}\n💵 السعر: {data['price']}\n👤 للتواصل: @{user_id}"
        bot.send_photo(CHANNEL_USERNAME, data["photo"], caption=caption)
        bot.send_message(user_id, "✅ تم قبول طلبك ونشره في القناة.")
    else:
        bot.send_message(user_id, "❌ تم رفض طلبك من قبل الإدارة.")
    
    del pending[user_id]
    save_json("pending", pending)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
