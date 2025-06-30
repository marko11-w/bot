import os
import json
from flask import Flask, request
import telebot
from telebot import types

# إعدادات
TOKEN = os.environ.get("7837218696:AAGSozPdf3hLT0bBjrgB3uExeuir-90Rvok") or "ضع_توكن_البوت"
ADMIN_ID = 7758666677  # آيدي الأدمن
CHANNEL_USERNAME = "@MARK01i"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ملفات التخزين
FILES = {
    "settings": "settings.json",
    "banned": "banned_users.json",
    "pending": "pending_requests.json"
}

# تحميل أو حفظ بيانات JSON
def load_json(name):
    try:
        with open(FILES[name], "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {} if name == "pending" else []

def save_json(name, data):
    with open(FILES[name], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# إعدادات افتراضية
if not os.path.exists(FILES["settings"]):
    save_json("settings", {
        "bot_active": True,
        "games": ["🎮 ببجي", "🔥 فري فاير", "⚽ بيس", "🎯 أخرى"],
        "messages": {
            "start": "👋 أهلاً بك في بوت بيع وتبادل الحسابات.\nأرسل صورة الحساب لبدء العملية.",
            "must_subscribe": f"🚫 يجب الاشتراك في القناة أولًا: {CHANNEL_USERNAME}"
        }
    })

# التحقق من الحظر
def is_banned(user_id):
    banned = load_json("banned")
    return user_id in banned

# نقطة تشغيل البوت
@app.route('/', methods=["GET", "POST"])
def webhook():
    if request.method == "POST":
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "ok"
    return "Bot running."

# /start
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        return bot.reply_to(message, "🚫 تم حظرك من استخدام هذا البوت.")
    
    settings = load_json("settings")
    if not settings.get("bot_active", True):
        return bot.reply_to(message, "🔒 البوت متوقف مؤقتًا من قبل الإدارة.")
    
    bot.send_message(user_id, settings["messages"]["start"])
    bot.send_message(user_id, "📸 الرجاء إرسال صورة الحساب للبيع أو التبادل.")
    bot.register_next_step_handler(message, receive_image)

# استقبال صورة الحساب
def receive_image(message):
    if not message.photo:
        return bot.reply_to(message, "📸 أرسل صورة وليس نصاً.")
    
    file_id = message.photo[-1].file_id
    pending = load_json("pending")
    user_id = str(message.from_user.id)
    pending[user_id] = {"photo": file_id}
    save_json("pending", pending)
    
    bot.send_message(message.chat.id, "📝 الآن أرسل وصف الحساب.")
    bot.register_next_step_handler(message, receive_description)

# استقبال الوصف
def receive_description(message):
    pending = load_json("pending")
    user_id = str(message.from_user.id)
    if user_id not in pending:
        return
    
    pending[user_id]["description"] = message.text
    save_json("pending", pending)

    # قائمة الألعاب
    settings = load_json("settings")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for game in settings["games"]:
        markup.add(game)
    bot.send_message(message.chat.id, "🎮 اختر نوع اللعبة:", reply_markup=markup)
    bot.register_next_step_handler(message, receive_game)

# استقبال نوع اللعبة
def receive_game(message):
    pending = load_json("pending")
    user_id = str(message.from_user.id)
    pending[user_id]["game"] = message.text
    save_json("pending", pending)

    bot.send_message(message.chat.id, "💵 اكتب السعر بالدولار ($):", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, receive_price)

# استقبال السعر
def receive_price(message):
    pending = load_json("pending")
    user_id = str(message.from_user.id)
    if user_id not in pending:
        return
    
    try:
        price = float(message.text)
        pending[user_id]["price"] = f"${price}"
    except:
        return bot.reply_to(message, "❌ يرجى إدخال رقم فقط.")
    
    save_json("pending", pending)

    bot.send_message(message.chat.id, "✅ تم استلام طلبك وسيتم مراجعته من الإدارة قريبًا.")

    # إرسال إلى الأدمن
    data = pending[user_id]
    caption = f"📌 طلب جديد من: @{message.from_user.username or 'بدون اسم'}\n\n" \
              f"🎮 اللعبة: {data['game']}\n" \
              f"💬 الوصف: {data['description']}\n" \
              f"💵 السعر: {data['price']}\n" \
              f"🆔 ID: {user_id}"

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")
    )
    bot.send_photo(ADMIN_ID, data["photo"], caption=caption, reply_markup=keyboard)

# زر القبول/الرفض
@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_") or c.data.startswith("reject_"))
def handle_decision(call):
    action, user_id = call.data.split("_")
    pending = load_json("pending")

    if user_id not in pending:
        return bot.answer_callback_query(call.id, "❌ الطلب غير موجود.")
    
    data = pending[user_id]
    if action == "accept":
        # النشر في القناة
        caption = f"🎮 {data['game']}\n💬 {data['description']}\n💵 السعر: {data['price']}\n👤 للتواصل: @{user_id}"
        bot.send_photo(CHANNEL_USERNAME, data["photo"], caption=caption)
        bot.send_message(user_id, "✅ تم قبول طلبك ونشره في القناة.")
    else:
        bot.send_message(user_id, "❌ تم رفض طلبك من قبل الإدارة.")
    
    del pending[user_id]
    save_json("pending", pending)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

# أوامر إدارية: /admin
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔧 إيقاف البوت", "▶️ تشغيل البوت")
    markup.add("📋 عرض الألعاب", "➕ إضافة لعبة", "🗑️ حذف لعبة")
    markup.add("🚫 حظر مستخدم", "🔓 رفع الحظر")
    bot.send_message(message.chat.id, "👮 لوحة تحكم الأدمن:", reply_markup=markup)

# (المزيد من الأوامر يمكن إضافتها حسب طلبك...)

# بدء Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
