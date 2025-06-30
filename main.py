import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import os  # لاستدعاء متغيرات البيئة مثل PORT و WEBHOOK_URL

TOKEN = "7837218696:AAGSozPdf3hLT0bBjrgB3uExeuir-90Rvok"
ADMIN_ID = 7758666677  # استبدل بـ ID الخاص بك
CHANNEL_USERNAME = "@MARK01i"  # رابط القناة الخاصة بك

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- لوحة أزرار الادمن ---
def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("تعديل الوصف", callback_data="edit_description"),
        InlineKeyboardButton("تعديل السعر", callback_data="edit_price"),
        InlineKeyboardButton("تعديل الصورة", callback_data="edit_image"),
        InlineKeyboardButton("حظر شخص", callback_data="ban_user"),
        InlineKeyboardButton("إيقاف البوت", callback_data="stop_bot")
    )
    return markup

# --- بداية البوت ---
@bot.message_handler(commands=["start"])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "مرحباً أيها الإدمن! اختر خياراً من القائمة:", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "مرحباً! هذا البوت خاص بالإدارة فقط.")

# --- التعامل مع أزرار الادمن ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "أنت غير مخوّل لاستخدام هذه الأزرار.")
        return

    if call.data == "edit_description":
        bot.answer_callback_query(call.id, "أرسل لي الوصف الجديد:")
        # هنا تضيف منطق استقبال الوصف الجديد (مثلاً انتظار رسالة الإدمن)
    elif call.data == "edit_price":
        bot.answer_callback_query(call.id, "أرسل لي السعر الجديد:")
        # منطق استقبال السعر الجديد
    elif call.data == "edit_image":
        bot.answer_callback_query(call.id, "أرسل لي الصورة الجديدة:")
        # منطق استقبال الصورة الجديدة
    elif call.data == "ban_user":
        bot.answer_callback_query(call.id, "أرسل لي معرف المستخدم لحظره:")
        # منطق الحظر
    elif call.data == "stop_bot":
        bot.answer_callback_query(call.id, "تم إيقاف البوت.")
        # منطق إيقاف البوت
    else:
        bot.answer_callback_query(call.id, "خيار غير معروف.")

# --- استقبال تحديثات الويب هوك ---
@app.route("/", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "", 200

# --- ضبط الويب هوك ---
def set_webhook():
    url = os.environ.get("WEBHOOK_URL")  # مثال: https://bot-production-7bab.up.railway.app/
    if url:
        bot.remove_webhook()
        bot.set_webhook(url=url)
    else:
        print("لم يتم تحديد WEBHOOK_URL في المتغيرات البيئية")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
