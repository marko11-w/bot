import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from flask import Flask, request
import os

TOKEN = "7837218696:AAGSozPdf3hLT0bBjrgB3uExeuir-90Rvok"
ADMIN_ID = 7758666677
CHANNEL_USERNAME = "@MARK01i"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# لتخزين بيانات المستخدمين أثناء الإدخال (حالة كل مستخدم)
user_states = {}
user_data = {}

# مراحل الإدخال
STATE_WAIT_PHOTO = 1
STATE_WAIT_DESCRIPTION = 2
STATE_WAIT_PRICE = 3
STATE_WAIT_TYPE = 4

# وظائف لإنشاء أزرار تعديل للإدمن
def admin_edit_buttons(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("تعديل الوصف", callback_data=f"edit_desc_{user_id}"),
        InlineKeyboardButton("تعديل السعر", callback_data=f"edit_price_{user_id}"),
        InlineKeyboardButton("تعديل نوع الحساب", callback_data=f"edit_type_{user_id}"),
        InlineKeyboardButton("تعديل الصورة", callback_data=f"edit_photo_{user_id}"),
        InlineKeyboardButton("نشر الإعلان", callback_data=f"publish_{user_id}"),
        InlineKeyboardButton("رفض الإعلان", callback_data=f"reject_{user_id}"),
    )
    return markup

# بدء المحادثة
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        bot.send_message(user_id, "مرحباً أيها الإدمن.")
        return

    bot.send_message(user_id, "أرسل صورة الحساب للبيع:")
    user_states[user_id] = STATE_WAIT_PHOTO
    user_data[user_id] = {}

# استقبال الصورة
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    if user_states.get(user_id) == STATE_WAIT_PHOTO:
        file_id = message.photo[-1].file_id
        user_data[user_id]['photo'] = file_id
        bot.send_message(user_id, "أرسل وصف الحساب:")
        user_states[user_id] = STATE_WAIT_DESCRIPTION
    elif user_states.get(user_id) == 'editing_photo':
        user_data[user_id]['photo'] = message.photo[-1].file_id
        bot.send_message(user_id, "تم تحديث الصورة بنجاح.")
        user_states[user_id] = None
        # إعادة إرسال البيانات للإدمن بعد التعديل
        send_for_admin(user_id)
    else:
        bot.send_message(user_id, "يرجى اتباع الخطوات.")

# استقبال الوصف
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == STATE_WAIT_DESCRIPTION)
def handle_description(message):
    user_id = message.from_user.id
    user_data[user_id]['description'] = message.text
    bot.send_message(user_id, "أرسل سعر الحساب (بالدولار):")
    user_states[user_id] = STATE_WAIT_PRICE

# استقبال السعر
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == STATE_WAIT_PRICE)
def handle_price(message):
    user_id = message.from_user.id
    price_text = message.text
    # تحقق أن السعر رقم
    try:
        price = float(price_text)
        user_data[user_id]['price'] = price
        bot.send_message(user_id, "أرسل نوع الحساب (مثل ببجي، بيس، فري فاير):")
        user_states[user_id] = STATE_WAIT_TYPE
    except ValueError:
        bot.send_message(user_id, "الرجاء إدخال سعر صحيح (رقم).")

# استقبال نوع الحساب
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == STATE_WAIT_TYPE)
def handle_type(message):
    user_id = message.from_user.id
    user_data[user_id]['type'] = message.text

    # أرسل للإدمن للمراجعة
    send_for_admin(user_id)

    bot.send_message(user_id, "تم إرسال عرضك إلى الإدارة للمراجعة. شكراً لك!")
    user_states[user_id] = None

# دالة لإرسال البيانات للإدمن
def send_for_admin(user_id):
    data = user_data.get(user_id)
    if not data:
        return
    caption = f"""عرض بيع حساب من المستخدم: @{bot.get_chat(user_id).username or user_id}
نوع الحساب: {data.get('type')}
السعر: {data.get('price')} دولار
الوصف: {data.get('description')}"""

    bot.send_photo(ADMIN_ID, data['photo'], caption=caption, reply_markup=admin_edit_buttons(user_id))

# التعامل مع أزرار تعديل الأدمن
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    user_id = call.from_user.id

    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "أنت غير مخوّل لاستخدام هذه الأزرار.")
        return

    if data.startswith("edit_desc_"):
        target_id = int(data.split("_")[2])
        bot.send_message(ADMIN_ID, f"أرسل الوصف الجديد للمستخدم {target_id}:")
        user_states[ADMIN_ID] = f"editing_desc_{target_id}"
        bot.answer_callback_query(call.id)

    elif data.startswith("edit_price_"):
        target_id = int(data.split("_")[2])
        bot.send_message(ADMIN_ID, f"أرسل السعر الجديد للمستخدم {target_id}:")
        user_states[ADMIN_ID] = f"editing_price_{target_id}"
        bot.answer_callback_query(call.id)

    elif data.startswith("edit_type_"):
        target_id = int(data.split("_")[2])
        bot.send_message(ADMIN_ID, f"أرسل نوع الحساب الجديد للمستخدم {target_id}:")
        user_states[ADMIN_ID] = f"editing_type_{target_id}"
        bot.answer_callback_query(call.id)

    elif data.startswith("edit_photo_"):
        target_id = int(data.split("_")[2])
        bot.send_message(ADMIN_ID, f"أرسل الصورة الجديدة للمستخدم {target_id}:")
        user_states[ADMIN_ID] = f"editing_photo_{target_id}"
        bot.answer_callback_query(call.id)

    elif data.startswith("publish_"):
        target_id = int(data.split("_")[1])
        publish_ad(target_id)
        bot.answer_callback_query(call.id, "تم نشر الإعلان في القناة.")

    elif data.startswith("reject_"):
        target_id = int(data.split("_")[1])
        bot.send_message(target_id, "تم رفض عرضك من قبل الإدارة.")
        bot.answer_callback_query(call.id, "تم رفض الإعلان.")
        # حذف البيانات المؤقتة
        if target_id in user_data:
            del user_data[target_id]

# استقبال ردود الادمن على تعديل البيانات
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, "").startswith("editing_"))
def handle_admin_edit(message):
    state = user_states[message.from_user.id]
    if not state:
        return
    parts = state.split("_")
    field = parts[1]  # desc, price, type, photo
    target_id = int(parts[2])
    
    if field == "desc":
        user_data[target_id]['description'] = message.text
        bot.send_message(ADMIN_ID, "تم تحديث الوصف.")
        send_for_admin(target_id)
        user_states[message.from_user.id] = None

    elif field == "price":
        try:
            price = float(message.text)
            user_data[target_id]['price'] = price
            bot.send_message(ADMIN_ID, "تم تحديث السعر.")
            send_for_admin(target_id)
            user_states[message.from_user.id] = None
        except ValueError:
            bot.send_message(ADMIN_ID, "الرجاء إدخال سعر صحيح (رقم).")

    elif field == "type":
        user_data[target_id]['type'] = message.text
        bot.send_message(ADMIN_ID, "تم تحديث نوع الحساب.")
        send_for_admin(target_id)
        user_states[message.from_user.id] = None

    elif field == "photo":
        bot.send_message(ADMIN_ID, "يرجى إرسال صورة جديدة وليس نصاً.")

# دالة النشر في القناة
def publish_ad(user_id):
    data = user_data.get(user_id)
    if not data:
        bot.send_message(ADMIN_ID, "لا توجد بيانات لنشرها.")
        return
    caption = f"""نوع الحساب: {data.get('type')}
السعر: {data.get('price')} دولار
الوصف: {data.get('description')}"""
    bot.send_photo(CHANNEL_USERNAME, data['photo'], caption=caption)
    bot.send_message(user_id, "تم نشر إعلانك في القناة.")
    # حذف البيانات بعد النشر
    del user_data[user_id]

# --- استقبال تحديثات الويب هوك ---
@app.route("/", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "", 200

# ضبط الويب هوك
def set_webhook():
    url = os.environ.get("WEBHOOK_URL")
    if url:
        bot.remove_webhook()
        bot.set_webhook(url=url)
    else:
        print("لم يتم تحديد WEBHOOK_URL")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


