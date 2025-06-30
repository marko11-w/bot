import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import os

TOKEN = "7837218696:AAGSozPdf3hLT0bBjrgB3uExeuir-90Rvok"
ADMIN_ID = 7758666677  # عدلها إلى أيديك

bot = telebot.TeleBot(TOKEN)

# حالة المستخدم (للمتابعة في أي خطوة تعديل أو إدخال)
user_states = {}
# بيانات المستخدمين المؤقتة
user_data = {}

# دالة لإرسال رسالة مع أزرار للإدمن لتعديل بيانات الحساب
def send_for_admin(user_id):
    data = user_data.get(user_id)
    if not data:
        return
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("تعديل الصورة", callback_data=f"edit_photo_{user_id}"),
        InlineKeyboardButton("تعديل الوصف", callback_data=f"edit_desc_{user_id}"),
        InlineKeyboardButton("تعديل السعر", callback_data=f"edit_price_{user_id}"),
        InlineKeyboardButton("تعديل اليوزر", callback_data=f"edit_user_{user_id}")
    )
    caption = f"""عرض حساب للشراء:

مستخدم: {data.get('user')}
نوع الحساب: {data.get('type')}
السعر: {data.get('price')} دولار
الوصف:
{data.get('description')}
"""
    # إرسال الصورة مع الكابتشن
    bot.send_photo(ADMIN_ID, data['photo_file_id'], caption=caption, reply_markup=markup)

# بداية التعامل مع المستخدم
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_states[user_id] = "waiting_photo"
    user_data[user_id] = {"user": f"@{message.from_user.username}" if message.from_user.username else str(user_id)}
    bot.send_message(user_id, "أرسل صورة حساب اللعبة التي تريد بيعها:")

# استقبال الصورة
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    if user_states.get(user_id) == "waiting_photo":
        file_id = message.photo[-1].file_id
        user_data[user_id]['photo_file_id'] = file_id
        user_states[user_id] = "waiting_type"
        bot.send_message(user_id, "أرسل نوع الحساب (مثلاً: ببجي، فري فاير، بيس، إلخ):")
    elif user_states.get(user_id) and user_states[user_id].startswith("editing_photo_"):
        target_id = int(user_states[user_id].split("_")[2])
        user_data[target_id]['photo_file_id'] = message.photo[-1].file_id
        bot.send_message(ADMIN_ID, "تم تحديث الصورة.")
        send_for_admin(target_id)
        user_states[user_id] = None

# استقبال نوع الحساب
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "waiting_type")
def handle_type(message):
    user_id = message.from_user.id
    user_data[user_id]['type'] = message.text
    user_states[user_id] = "waiting_desc"
    bot.send_message(user_id, "أرسل وصف الحساب:")

# استقبال الوصف
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "waiting_desc")
def handle_desc(message):
    user_id = message.from_user.id
    user_data[user_id]['description'] = message.text
    user_states[user_id] = "waiting_price"
    bot.send_message(user_id, "أرسل سعر الحساب (بالدولار):")

# استقبال السعر
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "waiting_price")
def handle_price(message):
    user_id = message.from_user.id
    text = message.text
    if not text.replace('.', '', 1).isdigit():
        bot.send_message(user_id, "من فضلك ارسل سعر صالح (رقم فقط).")
        return
    user_data[user_id]['price'] = text
    user_states[user_id] = None
    bot.send_message(user_id, "تم استلام بيانات حسابك. سيتم مراجعتها من قبل الإدارة.")

    # ارسال للادمن
    send_for_admin(user_id)

# التعامل مع أزرار الإدارة
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    admin_id = call.from_user.id
    if admin_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "ليس لديك صلاحية.")
        return

    if data.startswith("edit_"):
        parts = data.split("_")
        field = parts[1]  # photo, desc, price, user
        target_id = int(parts[2])
        user_states[admin_id] = f"editing_{field}_{target_id}"
        bot.answer_callback_query(call.id)
        bot.send_message(admin_id, f"أرسل {field} الجديد:")

# استقبال ردود تعديل الادمن
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id) and user_states[m.from_user.id].startswith("editing_"))
def handle_admin_edit(message):
    admin_id = message.from_user.id
    state = user_states.get(admin_id)
    if not state:
        return
    parts = state.split("_")
    field = parts[1]
    target_id = int(parts[2])

    if field == "photo":
        if message.content_type != 'photo':
            bot.send_message(admin_id, "الرجاء إرسال صورة فقط.")
            return
        user_data[target_id]['photo_file_id'] = message.photo[-1].file_id
        bot.send_message(admin_id, "تم تحديث الصورة.")
    elif field == "desc":
        user_data[target_id]['description'] = message.text
        bot.send_message(admin_id, "تم تحديث الوصف.")
    elif field == "price":
        text = message.text
        if not text.replace('.', '', 1).isdigit():
            bot.send_message(admin_id, "من فضلك ارسل سعر صالح (رقم فقط).")
            return
        user_data[target_id]['price'] = text
        bot.send_message(admin_id, "تم تحديث السعر.")
    elif field == "user":
        user_data[target_id]['user'] = message.text
        bot.send_message(admin_id, "تم تحديث اليوزر.")

    user_states[admin_id] = None
    send_for_admin(target_id)


if __name__ == "__main__":
    import os
    from flask import Flask, request

    app = Flask(__name__)

    @app.route('/', methods=['POST'])
    def webhook():
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "!", 200

    PORT = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=PORT)



