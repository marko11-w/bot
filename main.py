from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os

FAKE_BALANCE = 100.0
TOKEN = os.getenv("BOT_TOKEN")

def start(update, context):
    user = update.effective_user.first_name or "صديق"
    text = (f"مرحبًا {user} 👋\n"
            f"أهلاً بك في بوت الأرباح اليومية!\n"
            f"رصيدك الحالي: {FAKE_BALANCE:.2f} $ 💰")
    update.message.reply_text(text)

def balance(update, context):
    update.message.reply_text(f"💰 رصيدك الحالي هو: {FAKE_BALANCE:.2f} $")

def withdraw(update, context):
    args = context.args
    if not args or not args[0].isdigit():
        update.message.reply_text("❌ استخدم: /withdraw <المبلغ>")
        return
    amount = float(args[0])
    if amount < 10:
        update.message.reply_text("❌ الحد الأدنى للسحب هو 10 $")
    else:
        update.message.reply_text(
            f"✅ تم استلام طلب السحب بقيمة {amount:.2f} $\n"
            "📩 سيتم تحويل المبلغ خلال 24 ساعة (وهمياً 😅)"
        )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("withdraw", withdraw))

    updater.start_polling()
    print("🤖 البوت شغال...")
    updater.idle()

if __name__ == "__main__":
    main()
