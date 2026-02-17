import os
import datetime
import secrets
import time
import psycopg2
from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

DATABASE_URL = os.environ.get("DATABASE_URL")

# HASHLENMİŞ ŞİFRELER
SITE_PASSWORD_HASH = generate_password_hash("1806")
ADMIN_PASSWORD_HASH = generate_password_hash("0000")


# ------------------ DATABASE ------------------

def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name TEXT,
            content TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ------------------ LOGIN ------------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")

        if check_password_hash(SITE_PASSWORD_HASH, password):
            session["logged_in"] = True
            return redirect("/site")

    return """
    <html>
    <body style="background:#0f0c29;color:white;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Poppins,Arial;">
        <form method="POST" style="background:rgba(255,255,255,0.08);padding:40px;border-radius:20px;text-align:center;backdrop-filter:blur(10px);">
            <h2>Giriş Yap</h2>
            <input type="password" name="password" placeholder="Şifre" style="padding:12px;border:none;border-radius:12px;"><br><br>
            <button type="submit" style="padding:12px 25px;background:linear-gradient(90deg,#ff6a00,#ee0979);color:white;border:none;border-radius:30px;cursor:pointer;">Giriş</button>
        </form>
    </body>
    </html>
    """


# ------------------ ANA SITE ------------------

@app.route("/site", methods=["GET", "POST"])
def site():

    if not session.get("logged_in"):
        return redirect("/")

    conn = get_connection()
    c = conn.cursor()

    # SPAM KORUMA (5 saniye)
    if request.method == "POST":

        now = time.time()
        last_post = session.get("last_post_time", 0)

        if now - last_post < 5:
            return "<h2 style='color:red;text-align:center;'>Çok hızlı mesaj atıyorsun 😅 5 saniye bekle.</h2>"

        name = request.form.get("name") or "Anonim"
        content = request.form.get("content")

        if content and len(content) < 500:
            date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            c.execute(
                "INSERT INTO messages (name, content, date) VALUES (%s, %s, %s)",
                (name, content, date)
            )
            conn.commit()
            session["last_post_time"] = now

    c.execute("SELECT * FROM messages ORDER BY id DESC")
    messages = c.fetchall()
    conn.close()

    message_html = ""
    for msg in messages:
        message_html += f"""
        <div class='message'>
            <strong>{msg[1]}</strong> 
            <span class='date'>({msg[3]})</span>
            <p>{msg[2]}</p>
        </div>
        """

    return f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
    body {{
        margin:0;
        font-family:'Poppins', sans-serif;
        background: linear-gradient(135deg,#0f0c29,#302b63,#24243e);
        color:white;
        padding:40px;
    }}

    h2 {{
        text-align:center;
        font-weight:700;
        margin-bottom:30px;
    }}

    form {{
        max-width:600px;
        margin:0 auto;
    }}

    input, textarea {{
        width:100%;
        padding:14px;
        margin-top:12px;
        border:none;
        border-radius:15px;
        font-size:14px;
    }}

    textarea {{
        height:120px;
        resize:none;
    }}

    button {{
        margin-top:15px;
        padding:14px 30px;
        border:none;
        border-radius:30px;
        font-weight:500;
        background: linear-gradient(90deg,#ff6a00,#ee0979);
        color:white;
        cursor:pointer;
        transition:0.3s;
    }}

    button:hover {{
        transform:scale(1.07);
        box-shadow:0 10px 25px rgba(255,0,100,0.4);
    }}

    .message {{
        max-width:600px;
        margin:25px auto;
        background: rgba(255,255,255,0.07);
        padding:20px;
        border-radius:20px;
        backdrop-filter: blur(8px);
        animation:fadeIn 0.6s ease;
    }}

    .date {{
        opacity:0.6;
        font-size:12px;
    }}

    @keyframes fadeIn {{
        from {{opacity:0; transform:translateY(15px);}}
        to {{opacity:1; transform:translateY(0);}}
    }}
    </style>
    </head>

    <body>

    <h2>Sözler Gider, Yazılar Kalır</h2>

    <form method="POST">
    <input type="text" name="name" placeholder="İsmin (isteğe bağlı)">
    <textarea name="content" placeholder="Bir iz bırak..."></textarea>
    <button type="submit">Paylaş</button>
    </form>

    {message_html}

    </body>
    </html>
    """


# ------------------ ADMIN ------------------

@app.route("/x9a7k-admin-portal", methods=["GET", "POST"])
def admin_panel():

    if request.method == "POST" and request.form.get("admin_pass"):
        if check_password_hash(ADMIN_PASSWORD_HASH, request.form.get("admin_pass")):
            session["admin"] = True

    if not session.get("admin"):
        return """
        <html>
        <body style="background:black;color:white;text-align:center;padding-top:100px;">
        <h2>Admin Girişi</h2>
        <form method="POST">
            <input type="password" name="admin_pass" placeholder="Admin Şifre">
            <button type="submit">Giriş</button>
        </form>
        </body>
        </html>
        """

    conn = get_connection()
    c = conn.cursor()

    if request.method == "POST" and request.form.get("delete_id"):
        c.execute("DELETE FROM messages WHERE id=%s", (request.form.get("delete_id"),))
        conn.commit()

    c.execute("SELECT * FROM messages ORDER BY id DESC")
    messages = c.fetchall()
    conn.close()

    message_html = ""
    for msg in messages:
        message_html += f"""
        <div style='background:#222;padding:10px;margin:10px;border-radius:10px;'>
            <strong>{msg[1]}</strong> ({msg[3]})
            <p>{msg[2]}</p>
            <form method='POST'>
                <input type='hidden' name='delete_id' value='{msg[0]}'>
                <button style='background:red;color:white;border:none;padding:5px 10px;border-radius:5px;'>Sil</button>
            </form>
        </div>
        """

    return f"""
    <html>
    <body style="background:black;color:white;padding:20px;">
    <h2>Admin Panel</h2>
    {message_html}
    </body>
    </html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
