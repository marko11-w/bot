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
    caption = f"📤 طلب جديد\n🎮 {state['game']}\n📝 {state['desc']}\n💵 {state['price']}$\n👤 @{call.from_user.username or 'لا يوجد'}\n🆔 {user_id}"
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def process_request(call):
    uid = call.data.split("_")[1]
    data = pending.get(uid)
    if not data: return
    if call.data.startswith("accept_"):
        caption = f"🔥 حساب جديد للبيع!\n🎮 {data['game']}\n📝 {data['desc']}\n💵 {data['price']}$\n📩 تواصل مع: @{call.from_user.username or 'لا يوجد'}"
        bot.send_photo(CHANNEL_USERNAME, data["photo"], caption=caption)
        bot.send_message(int(uid), "✅ تم نشر حسابك.")
    else:
        bot.send_message(int(uid), "❌ تم رفض طلبك.")
    del pending[uid]
    save_json("pending_requests.json", pending)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def start_edit(call):
    uid = call.data.split("_")[1]
    if uid not in pending: return
    user_states[call.from_user.id] = {"edit_user": uid, "step": "choose_edit"}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("✏️ تعديل الوصف", "💰 تعديل السعر")
    markup.row("🖼️ تعديل الصورة", "❌ إلغاء")
    bot.send_message(call.message.chat.id, "🔧 اختر ما تريد تعديله:", reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "choose_edit")
def handle_edit_choice(message):
    uid = user_states[message.from_user.id]["edit_user"]
    if message.text == "✏️ تعديل الوصف":
        bot.send_message(message.chat.id, "✏️ أرسل الوصف الجديد:")
        user_states[message.from_user.id]["step"] = "new_desc"
    elif message.text == "💰 تعديل السعر":
        bot.send_message(message.chat.id, "💰 أرسل السعر الجديد:")
        user_states[message.from_user.id]["step"] = "new_price"
    elif message.text == "🖼️ تعديل الصورة":
        bot.send_message(message.chat.id, "📸 أرسل الصورة الجديدة:")
        user_states[message.from_user.id]["step"] = "new_photo"
    else:
        user_states.pop(message.from_user.id)
        bot.send_message(message.chat.id, "❌ تم الإلغاء.")
        @bot.message_handler(content_types=["text", "photo"])
def handle_admin_updates(message):
    uid = user_states.get(message.from_user.id, {}).get("edit_user")
    step = user_states.get(message.from_user.id, {}).get("step")
    if not uid or uid not in pending: return

    if step == "new_desc":
        pending[uid]["desc"] = message.text
    elif step == "new_price":
        try:
            pending[uid]["price"] = float(message.text)
        except:
            return bot.send_message(message.chat.id, "❌ أدخل رقمًا صحيحًا.")
    elif step == "new_photo" and message.content_type == "photo":
        pending[uid]["photo"] = message.photo[-1].file_id
    else:
        return

    save_json("pending_requests.json", pending)
    bot.send_message(message.chat.id, "✅ تم التعديل.")
    user_states.pop(message.from_user.id)

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 الألعاب", "✏️ الرسائل")
    markup.row("🚫 حظر", "✅ رفع الحظر")
    markup.row("🟢 تشغيل البوت", "🔴 إيقاف البوت")
    markup.row("📥 عرض الطلبات المعلقة", "📣 إرسال جماعي")
    bot.send_message(message.chat.id, "🛠️ لوحة تحكم الأدمن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "📥 عرض الطلبات المعلقة")
def show_pending(message):
    if not pending:
        return bot.send_message(message.chat.id, "📭 لا توجد طلبات معلقة حالياً.")
    for uid, data in pending.items():
        caption = f"📌 طلب من المستخدم {uid}\n🎮 {data['game']}\n📝 {data['desc']}\n💵 {data['price']}$"
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ قبول", callback_data=f"accept_{uid}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{uid}")
        )
        markup.add(types.InlineKeyboardButton("✏️ تعديل", callback_data=f"edit_{uid}"))
        bot.send_photo(message.chat.id, data['photo'], caption=caption, reply_markup=markup)
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
    
