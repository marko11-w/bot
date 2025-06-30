import os, json
from flask import Flask, request
import telebot
from telebot import types

TOKEN = "7837218696:AAGSozPdf3hLT0bBjrgB3uExeuir-90Rvok"
ADMIN_ID = 7758666677
CHANNEL_USERNAME = "@MARK01i"

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)

def load_json(path, default):
    try: return json.load(open(path, "r", encoding="utf-8"))
    except: return default

def save_json(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

settings = load_json("settings.json", {
    "games": ["🎮 ببجي", "🔥 فري فاير", "⚽ بيس", "🎯 أخرى"],
    "bot_active": True,
    "messages": {
        "start": "👋 أهلاً بك في بوت بيع وتبادل الحسابات.",
        "must_subscribe": "🚫 يجب الاشتراك في القناة أولًا: @MARK01i"
    }
})
banned_users = load_json("banned_users.json", [])
pending = load_json("pending_requests.json", {})
user_states = {}

def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    if not settings["bot_active"] and user_id != ADMIN_ID:
        return bot.send_message(user_id, "🚫 البوت متوقف مؤقتًا.")
    if user_id in banned_users:
        return bot.send_message(user_id, "🚫 تم حظرك.")
    if not is_subscribed(user_id):
        return bot.send_message(user_id, settings["messages"]["must_subscribe"])
    bot.send_message(user_id, settings["messages"]["start"])
    bot.send_message(user_id, "📸 أرسل صورة الحساب.")
    user_states[user_id] = {"step": "photo"}

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    user_id = message.from_user.id
    if user_states.get(user_id, {}).get("step") != "photo": return
    user_states[user_id]["photo"] = message.photo[-1].file_id
    user_states[user_id]["step"] = "desc"
    bot.send_message(user_id, "📝 اكتب وصف الحساب:")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "desc")
def handle_desc(message):
    user_id = message.from_user.id
    user_states[user_id]["desc"] = message.text
    user_states[user_id]["step"] = "game"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for g in settings["games"]: markup.add(g)
    bot.send_message(user_id, "🎮 اختر نوع اللعبة:", reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "game")
def handle_game(message):
    user_id = message.from_user.id
    game = message.text
    if game not in settings["games"]:
        return bot.send_message(user_id, "❌ اختر لعبة من القائمة.")
    user_states[user_id]["game"] = game
    user_states[user_id]["step"] = "price"
    bot.send_message(user_id, "💰 أدخل السعر بالدولار:")

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📥 الطلبات المعلقة", callback_data="admin_pending"),
        types.InlineKeyboardButton("📋 الألعاب", callback_data="admin_games"),
        types.InlineKeyboardButton("✏️ الرسائل", callback_data="admin_msgs"),
        types.InlineKeyboardButton("🚫 حظر", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ رفع الحظر", callback_data="admin_unban"),
        types.InlineKeyboardButton("🔴 إيقاف البوت", callback_data="admin_stop"),
        types.InlineKeyboardButton("🟢 تشغيل البوت", callback_data="admin_start"),
    )
    bot.send_message(message.chat.id, "🔧 لوحة التحكم:\nاختر العملية التي ترغب بإدارتها 👇", reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "price")
def handle_price(message):
    user_id = message.from_user.id
    try: price = float(message.text)
    except: return bot.send_message(user_id, "❌ أدخل رقمًا صحيحًا.")
    user_states[user_id]["price"] = price
    user_states[user_id]["step"] = "confirm"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ إرسال الطلب", callback_data="confirm_submit"))
    bot.send_message(user_id, "هل تريد إرسال الطلب؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_submit")
def submit_request(call):
    user_id = call.from_user.id
    state = user_states.get(user_id, {})
    if not state: return
    caption = f"📤 طلب جديد\\n🎮 {state['game']}\\n📝 {state['desc']}\\n💵 {state['price']}$\\n👤 @{call.from_user.username or 'لا يوجد'}\\n🆔 {user_id}"
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")
    )
    markup.add(types.InlineKeyboardButton("✏️ تعديل", callback_data=f"edit_{user_id}"))
    msg = bot.send_photo(ADMIN_ID, state["photo"], caption=caption, reply_markup=markup)
    pending[str(user_id)] = {**state, "msg_id": msg.message_id}
    save_json("pending_requests.json", pending)
    bot.send_message(user_id, "📬 تم إرسال الطلب.")
    user_states.pop(user_id)

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    @bot.callback_query_handler(func=lambda call: call.data == "admin_games")
def edit_games(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.send_message(call.message.chat.id, "📝 أرسل قائمة الألعاب الجديدة، كل لعبة في سطر.")
    user_states[call.from_user.id] = {"step": "edit_games"}

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "edit_games")
def save_games(message):
    @bot.callback_query_handler(func=lambda call: call.data == "admin_msgs")
def edit_messages(call):
    if call.from_user.id != ADMIN_ID:
        return
    keys = list(settings["messages"].keys())
    txt = "✏️ الرسائل القابلة للتعديل:\n"
    txt += "\n".join([f"- {k}" for k in keys])
    txt += "\n\n📥 أرسل اسم الرسالة (مثل: start) يليها النص الجديد، مفصول بـ | هكذا:\n\nمثال:\nstart|مرحبًا بك!"
    user_states[call.from_user.id] = {"step": "edit_message"}
    bot.send_message(call.message.chat.id, txt)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "edit_message")
def save_message(message):
    @bot.callback_query_handler(func=lambda call: call.data == "admin_pending")
def show_pending_requests(call):
    if call.from_user.id != ADMIN_ID:
        return
    if not pending:
        return bot.send_message(call.message.chat.id, "📭 لا توجد طلبات معلقة.")
    
    for user_id, data in pending.items():
        try:
            caption = f"🎮 {data['game']}\n📝 {data['desc']}\n💵 {data['price']}$\n👤 @{data.get('username', 'لا يوجد')}\n🆔 {user_id}"
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_id}"),
                types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")
            )
            markup.add(types.InlineKeyboardButton("✏️ تعديل", callback_data=f"edit_{user_id}"))
            bot.send_photo(call.message.chat.id, data["photo"], caption=caption, reply_markup=markup)
        except Exception as e:
            print(f"خطأ في عرض طلب {user_id}: {e}")
    try:
        key, val = message.text.split("|", 1)
        key = key.strip()
        if key not in settings["messages"]:
            return bot.send_message(message.chat.id, "❌ المفتاح غير موجود.")
        settings["messages"][key] = val.strip()
        save_json("settings.json", settings)
        bot.send_message(message.chat.id, f"✅ تم تحديث رسالة: {key}")
    except:
        bot.send_message(message.chat.id, "❌ تنسيق غير صحيح. استخدم المفتاح | الرسالة.")
    user_states.pop(message.from_user.id)
    games_list = message.text.strip().split('\n')
    settings["games"] = games_list
    save_json("settings.json", settings)
    bot.send_message(message.chat.id, "✅ تم تحديث قائمة الألعاب.")
    user_states.pop(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📥 الطلبات المعلقة", callback_data="admin_pending"),
        types.InlineKeyboardButton("📋 الألعاب", callback_data="admin_games"),
        types.InlineKeyboardButton("✏️ الرسائل", callback_data="admin_msgs"),
        types.InlineKeyboardButton("🚫 حظر", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ رفع الحظر", callback_data="admin_unban"),
        types.InlineKeyboardButton("🔴 إيقاف البوت", callback_data="admin_stop"),
        types.InlineKeyboardButton("🟢 تشغيل البوت", callback_data="admin_start"),
    )
    bot.send_message(message.chat.id, "🔧 لوحة التحكم:\nاختر العملية التي ترغب بإدارتها 👇", reply_markup=markup)

@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200

@app.route("/", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
