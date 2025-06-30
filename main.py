import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import os

TOKEN = "7837218696:AAGSozPdf3hLT0bBjrgB3uExeuir-90Rvok"
ADMIN_ID = 7758666677
CHANNEL_USERNAME = "@MARK01i"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Dictionary to temporarily store sale submissions keyed by user_id
pending_sales = {}

# --- لوحة أزرار الادمن ---
def admin_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("تعديل الوصف", callback_data="edit_description"),
        InlineKeyboardButton("تعديل السعر", callback_data="edit_price"),
        InlineKeyboardButton("تعديل الصورة", callback_data="edit_image"),
        InlineKeyboardButton("حظر شخص", callback_data="ban_user"),
        InlineKeyboardButton("إيقاف البوت", callback_data="stop_bot")
    )
    return markup

# --- رسالة البداية ---
@bot.message_handler(commands=["start"])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "مرحباً أيها الإدمن! اختر خياراً من القائمة:", reply_markup=admin_menu())
    else:
        bot.send_message(message.chat.id, 
            "مرحباً! يمكنك هنا عرض حسابك للبيع. \n"
            "أرسل صورة الحساب ثم الوصف والسعر في رسالة واحدة.\n"
            "سيراجع الإدمن عرضك وينشره إذا تمت الموافقة.")

# --- استقبال صور الحساب مع الوصف والسعر ---
@bot.message_handler(content_types=['photo', 'text'])
def handle_sale_submission(message):
    user_id = message.from_user.id

    # فقط للمستخدمين غير الادمن
    if user_id == ADMIN_ID:
        return

    # نتحقق إن كانت رسالة تحتوي على صورة مع شرح وسعر (مثلاً في caption)
    if message.content_type == 'photo':
        caption = message.caption
        if not caption:
            bot.reply_to(message, "يرجى إضافة وصف وسعر في وصف الصورة (caption).")
            return
        # حفظ بيانات البيع مؤقتاً
        pending_sales[user_id] = {
            'photo_file_id': message.photo[-1].file_id,
            'caption': caption
        }
        bot.reply_to(message, "تم استلام عرضك. انتظر موافقة الإدارة.")
        
        # إرسال للإدمن مع أزرار الموافقة والرفض
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("موافقة ✅", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("رفض ❌", callback_data=f"reject_{user_id}")
        )
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
                       caption=f"عرض جديد من @{message.from_user.username or message.from_user.first_name}:\n{caption}",
                       reply_markup=markup)
    else:
        # يمكن إضافة منطق استقبال رسائل نصية أو غيرها إذا تريد
        pass

# --- التعامل مع أزرار الادمن (موافقة/رفض) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "أنت غير مخوّل لاستخدام هذه الأزرار.")
        return

    data = call.data
    if data.startswith("approve_"):
        target_id = int(data.split("_")[1])
        sale = pending_sales.get(target_id)
        if sale:
            # نشر العرض في القناة
            bot.send_photo(CHANNEL_USERNAME, sale['photo_file_id'], caption=sale['caption'])
            bot.answer_callback_query(call.id, "تم نشر العرض في القناة.")
            bot.send_message(target_id, "تمت الموافقة على عرضك ونشره في القناة.")
            del pending_sales[target_id]
        else:
            bot.answer_callback_query(call.id, "العرض غير موجود أو تم التعامل معه سابقاً.")
    elif data.startswith("reject_"):
        target_id = int(data.split("_")[1])
        if target_id in pending_sales:
            bot.send_message(target_id, "تم رفض عرضك من قبل الإدارة.")
            bot.answer_callback_query(call.id, "تم رفض العرض.")
            del pending_sales[target_id]
        else:
            bot.answer_callback_query(call.id, "العرض غير موجود أو تم التعامل معه سابقاً.")
    else:
        # معالجة باقي أزرار الادمن هنا حسب الكود السابق
        if data == "edit_description":
            bot.answer_callback_query(call.id, "أرسل لي الوصف الجديد:")
            # ... منطق التعديل
        elif data == "edit_price":
            bot.answer_callback_query(call.id, "أرسل لي السعر الجديد:")
            # ...
        elif data == "edit_image":
            bot.answer_callback_query(call.id, "أرسل لي الصورة الجديدة:")
            # ...
        elif data == "ban_user":
            bot.answer_callback_query(call.id, "أرسل لي معرف المستخدم لحظره:")
            # ...
        elif data == "stop_bot":
            bot.answer_callback_query(call.id, "تم إيقاف البوت.")
            # ...

# --- استقبال تحديثات الويب هوك ---
@app.route("/", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "", 200

# --- ضبط الويب هوك ---
def set_webhook():
    url = os.environ.get("WEBHOOK_URL")
    if url:
        bot.remove_webhook()
        bot.set_webhook(url=url)
    else:
        print("لم يتم تحديد WEBHOOK_URL في المتغيرات البيئية")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

