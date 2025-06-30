import os
from flask import Flask, request
import telebot
from telebot import types

TOKEN = "7837218696:AAGSozPdf3hLT0bBjrgB3uExeuir-90Rvok"
ADMIN_ID = 7758666677  # غيره إلى الايدي مالك البوت

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# بيانات الحسابات المعروضة للبيع كمثال
accounts_for_sale = {}

# قائمة المحظورين (مثال)
banned_users = set()

def admin_only(func):
    def wrapper(message):
        if message.from_user.id == ADMIN_ID:
            return func(message)
        else:
            bot.send_message(message.chat.id, "هذه الأوامر مخصصة للإدمن فقط.")
    return wrapper

# لوحة التحكم - أزرار رئيسية
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("بيع حساب", callback_data="sell_account"),
        types.InlineKeyboardButton("تعديل الوصف", callback_data="edit_description"),
        types.InlineKeyboardButton("تعديل السعر", callback_data="edit_price"),
        types.InlineKeyboardButton("تعديل الصورة", callback_data="edit_image"),
        types.InlineKeyboardButton("إيقاف البوت", callback_data="stop_bot"),
        types.InlineKeyboardButton("حظر مستخدم", callback_data="ban_user")
    )
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "مرحباً! اختر خياراً من القائمة:", reply_markup=main_menu())

# التعامل مع ضغط الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "هذه الأوامر للإدمن فقط.")
        return
    
    if call.data == "sell_account":
        bot.answer_callback_query(call.id, "أرسل صورة الحساب مع وصف وسعر.")
        msg = bot.send_message(call.message.chat.id, "أرسل صورة الحساب مع الوصف (نص مع الصورة).")
        bot.register_next_step_handler(msg, receive_account_info)
    
    elif call.data == "edit_description":
        bot.answer_callback_query(call.id, "أرسل رقم الحساب لتعديل الوصف.")
        msg = bot.send_message(call.message.chat.id, "أرسل رقم الحساب:")
        bot.register_next_step_handler(msg, edit_description_step)
        
    elif call.data == "edit_price":
        bot.answer_callback_query(call.id, "أرسل رقم الحساب لتعديل السعر.")
        msg = bot.send_message(call.message.chat.id, "أرسل رقم الحساب:")
        bot.register_next_step_handler(msg, edit_price_step)
    
    elif call.data == "edit_image":
        bot.answer_callback_query(call.id, "أرسل رقم الحساب لتعديل الصورة.")
        msg = bot.send_message(call.message.chat.id, "أرسل رقم الحساب:")
        bot.register_next_step_handler(msg, edit_image_step)
    
    elif call.data == "stop_bot":
        bot.answer_callback_query(call.id, "تم إيقاف البوت مؤقتاً.")
        # يمكنك وضع منطق الإيقاف أو رد معين هنا
        bot.send_message(call.message.chat.id, "البوت متوقف حالياً (وظيفة غير مفعلة).")
    
    elif call.data == "ban_user":
        bot.answer_callback_query(call.id, "أرسل ايدي المستخدم للحظر.")
        msg = bot.send_message(call.message.chat.id, "أرسل ايدي المستخدم:")
        bot.register_next_step_handler(msg, ban_user_step)

# استلام بيانات الحساب للبيع
def receive_account_info(message):
    if message.photo:
        caption = message.caption if message.caption else ""
        accounts_for_sale[message.message_id] = {
            "photo_file_id": message.photo[-1].file_id,
            "description": caption,
            "price": None
        }
        bot.send_message(message.chat.id, "تم استلام الصورة والوصف. الآن أرسل السعر (بالأرقام فقط).")
        bot.register_next_step_handler(message, receive_price_step, message.message_id)
    else:
        bot.send_message(message.chat.id, "الرجاء إرسال صورة مع الوصف.")
        return

def receive_price_step(message, msg_id):
    try:
        price = float(message.text)
        accounts_for_sale[msg_id]["price"] = price
        bot.send_message(message.chat.id, f"تم إضافة الحساب للسوق:\nالوصف: {accounts_for_sale[msg_id]['description']}\nالسعر: {price} $")
        # هنا يمكنك نشر الحساب في القناة أو حفظه في قاعدة بيانات
    except:
        bot.send_message(message.chat.id, "الرجاء إدخال سعر صحيح بالأرقام فقط.")
        bot.register_next_step_handler(message, receive_price_step, msg_id)

# تعديل الوصف
def edit_description_step(message):
    try:
        msg_id = int(message.text)
        if msg_id in accounts_for_sale:
            msg = bot.send_message(message.chat.id, "أرسل الوصف الجديد:")
            bot.register_next_step_handler(msg, save_new_description, msg_id)
        else:
            bot.send_message(message.chat.id, "رقم الحساب غير موجود.")
    except:
        bot.send_message(message.chat.id, "الرجاء إدخال رقم صحيح.")

def save_new_description(message, msg_id):
    accounts_for_sale[msg_id]["description"] = message.text
    bot.send_message(message.chat.id, "تم تعديل الوصف بنجاح.")

# تعديل السعر
def edit_price_step(message):
    try:
        msg_id = int(message.text)
        if msg_id in accounts_for_sale:
            msg = bot.send_message(message.chat.id, "أرسل السعر الجديد (بالأرقام فقط):")
            bot.register_next_step_handler(msg, save_new_price, msg_id)
        else:
            bot.send_message(message.chat.id, "رقم الحساب غير موجود.")
    except:
        bot.send_message(message.chat.id, "الرجاء إدخال رقم صحيح.")

def save_new_price(message, msg_id):
    try:
        price = float(message.text)
        accounts_for_sale[msg_id]["price"] = price
        bot.send_message(message.chat.id, "تم تعديل السعر بنجاح.")
    except:
        bot.send_message(message.chat.id, "الرجاء إدخال سعر صحيح.")

# تعديل الصورة
def edit_image_step(message):
    try:
        msg_id = int(message.text)
        if msg_id in accounts_for_sale:
            msg = bot.send_message(message.chat.id, "أرسل الصورة الجديدة:")
            bot.register_next_step_handler(msg, save_new_image, msg_id)
        else:
            bot.send_message(message.chat.id, "رقم الحساب غير موجود.")
    except:
        bot.send_message(message.chat.id, "الرجاء إدخال رقم صحيح.")

def save_new_image(message, msg_id):
    if message.photo:
        accounts_for_sale[msg_id]["photo_file_id"] = message.photo[-1].file_id
        bot.send_message(message.chat.id, "تم تعديل الصورة بنجاح.")
    else:
        bot.send_message(message.chat.id, "الرجاء إرسال صورة فقط.")

# حظر مستخدم
def ban_user_step(message):
    try:
        user_id = int(message.text)
        banned_users.add(user_id)
        bot.send_message(message.chat.id, f"تم حظر المستخدم {user_id}.")
    except:
        bot.send_message(message.chat.id, "الرجاء إدخال ايدي صحيح.")

# مثال: منع المستخدمين المحظورين من استخدام البوت
@bot.message_handler(func=lambda m: m.from_user.id in banned_users)
def banned_message(message):
    bot.send_message(message.chat.id, "أنت محظور من استخدام البوت.")

# ويب هوك لاستقبال التحديثات من Telegram
@app.route("/", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "", 200

if __name__ == "__main__":
    # احذف الويب هوك القديم
    bot.remove_webhook()
    # اضبط الويب هوك مع رابطك (غير الرابط أدناه إلى رابطك الحقيقي)
    WEBHOOK_URL = "https://bot-production-7bab.up.railway.app/"
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
