# from flask import Flask, request, jsonify, render_template, redirect
# from flask_cors import CORS

# app = Flask(__name__)

# app.config["SECRET_KEY"] = "secret123"
# app.config["CORS_HEADERS"] = "Content-Type"

# CORS(app, supports_credentials=True)
# import docx
# from PyPDF2 import PdfReader

# from flask_login import LoginManager, login_user, login_required, logout_user, current_user
# from werkzeug.security import generate_password_hash, check_password_hash
# from datetime import datetime
# import os, pickle, time
# import pytesseract
# from PIL import Image

# from models import db, User, Scan
# from utils.preprocess import clean_text
# from utils.url_blacklist import BLACKLIST
# from functools import wraps







# def admin_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         if not current_user.is_authenticated or not current_user.is_admin:
#             return jsonify({"error": "Admin only"}), 403
#         return f(*args, **kwargs)
#     return decorated


# # ---------------- CONFIG ---------------- #

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# app.config['SESSION_COOKIE_HTTPONLY'] = True

# db.init_app(app)

# CORS(app,
#      supports_credentials=True,
#      origins=["http://127.0.0.1:5500","http://localhost:5500"])

# login_manager = LoginManager()
# login_manager.init_app(app)
# # @login_manager.unauthorized_handler
# # def unauthorized():
# #     return jsonify({"error": "Unauthorized"}), 401

# login_manager.login_view = "login"

# app.config.update(
#     SESSION_COOKIE_SAMESITE="None",
#     SESSION_COOKIE_SECURE=False,  # True only if HTTPS
#     SESSION_COOKIE_HTTPONLY=True
# )


# # 🔥 Tesseract
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# # 🔥 Load ML model
# pipeline = pickle.load(open(os.path.join(BASE_DIR, "model", "pipeline.pkl"), "rb"))
# threshold = float(open(os.path.join(BASE_DIR, "model", "threshold.txt")).read())

# # ---------------- USER ---------------- #
# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))

# @app.route("/")
# def home():
#     return redirect("/scan")

# # ---------------- AUTH ---------------- #

# @app.route("/register", methods=["GET", "POST"])
# def register():

#     if request.method == "GET":
#         return render_template("register.html")

#     data = request.form

#     username = data.get("username", "").strip().lower()
#     password = data.get("password", "").strip()

#     if not username or not password:
#         return "Missing fields ❌"

#     if User.query.filter_by(username=username).first():
#         return "User already exists ❌"

#     is_admin = User.query.count() == 0

#     user = User(
#         username=username,
#         password=generate_password_hash(password),
#         is_admin=is_admin
#     )

#     db.session.add(user)
#     db.session.commit()

#     return redirect("/login")

# @app.route("/login", methods=["GET", "POST"])
# def login():

#     if request.method == "GET":
#         return render_template("login.html")

#     username = request.form.get("username")
#     password = request.form.get("password")

#     user = User.query.filter_by(username=username).first()

#     if user and check_password_hash(user.password, password):
#         login_user(user)
#         return redirect("/scan")

#     return "Invalid username or password ❌"
    

# from werkzeug.utils import secure_filename

# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# @app.route("/scan-file", methods=["POST"])
# def scan_file():
#     try:
#         if "file" not in request.files:
#             return jsonify({"error": "No file uploaded"}), 400

#         file = request.files["file"]

#         if file.filename == "":
#             return jsonify({"error": "Empty filename"}), 400

#         filename = secure_filename(file.filename)
#         filepath = os.path.join("uploads", filename)

#         os.makedirs("uploads", exist_ok=True)
#         file.save(filepath)

#         # 🔥 TEMP TEST (important)
#         return jsonify({
#             "risk": "Safe",
#             "confidence": 90,
#             "pros": ["File processed"],
#             "cons": [],
#             "text": "Test content"
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @app.route("/logout")
# def logout():
#     logout_user()
#     return jsonify({"message": "Logged out"})

# @app.route("/scan")
# def scan_page():
#     return render_template("scan.html")

# # ---------------- ALERTS ---------------- #

# @app.route("/alerts")
# def alerts():
#     return jsonify([
#         {
#             "type": "Phishing",
#             "message": "Fake bank login pages are targeting users",
#             "level": "High"
#         },
#         {
#             "type": "Lottery Scam",
#             "message": "WhatsApp lottery scams increasing rapidly",
#             "level": "Medium"
#         },
#         {
#             "type": "KYC Fraud",
#             "message": "Scammers posing as bank KYC agents",
#             "level": "High"
#         }
#     ])
# # ---------------- NOTIFICATIONS ---------------- #

# notifications = {}

# def add_notification(msg):
#     user_id = current_user.id

#     if user_id not in notifications:
#         notifications[user_id] = []

#     notifications[user_id].append({
#         "msg": msg,
#         "time": datetime.now().strftime("%H:%M:%S")
#     })

# @app.route("/notifications")
# def get_notifications():
#     user_id = current_user.id
#     return jsonify(notifications.get(user_id, [])[-5:])

# # ---------------- SCAN ---------------- #

# @app.route("/predict", methods=["POST"])
# def predict():
#     text = request.json.get("text", "")
#     result = analyze_text(text)
#     return result

# # ---------------- CORE ---------------- #

# import re
# from urllib.parse import urlparse

# SHORTENERS = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "rb.gy"]

# def extract_urls(text):
#     return re.findall(r'(https?://\S+|www\.\S+)', text)

# import socket

# def analyze_url(url):
#     parsed = urlparse(url if url.startswith("http") else "http://" + url)
#     domain = parsed.netloc.lower()

#     risk = 0
#     reasons = []

#     # 🔗 1. URL Shortener
#     if any(short in domain for short in SHORTENERS):
#         risk += 30
#         reasons.append("Shortened URL detected (destination hidden)")

#     # 🧠 2. Suspicious Keywords
#     suspicious_keywords = ["login", "verify", "secure", "update", "bank", "account"]
#     if any(k in url.lower() for k in suspicious_keywords):
#         risk += 20
#         reasons.append("Contains phishing-related keywords")

#     # 🌐 3. Fake Domain Structure
#     if domain.count('.') > 3:
#         risk += 15
#         reasons.append("Unusually complex domain structure")

#     # 🔍 4. Hyphen Trick
#     if "-" in domain:
#         risk += 10
#         reasons.append("Domain uses hyphen (common phishing trick)")

#     # 🚨 5. IP Address Instead of Domain
#     if re.match(r"\d+\.\d+\.\d+\.\d+", domain):
#         risk += 25
#         reasons.append("Uses IP address instead of domain name")

#     # 🔌 6. Domain resolution check
#     try:
#         socket.gethostbyname(domain)
#     except:
#         risk += 20
#         reasons.append("Domain does not resolve (suspicious)")
        
#         # 🚨 7. Blacklist match
#     if any(bad in url.lower() for bad in BLACKLIST):
#      risk += 40
#     reasons.append("URL matches known scam patterns database")
    
#     # 🌐 8. Suspicious TLD
#     if domain.endswith((".xyz", ".top", ".tk", ".ml")):
#      risk += 20
#     reasons.append("Uses suspicious top-level domain")

#     return risk, reasons


# def explain_scam(text):
#     t = text.lower()

#     pros = []
#     cons = []
#     score = 0

#     # 🔗 URL ANALYSIS
#     urls = extract_urls(text)
#     for url in urls:
#         url_risk, url_reasons = analyze_url(url)
#         score += url_risk
#         for r in url_reasons:
#          cons.append(f"🔗 Link Risk: {r}")
#          if urls:
#            cons.append(f"Detected {len(urls)} link(s) in the message")

#     # 📱 PHONE NUMBER DETECTION
#     if re.search(r'\+?\d{10,}', text):
#         score += 10
#         cons.append("Contains phone number (common in scam outreach)")

#     # 🚨 URGENCY
#     if any(word in t for word in ["urgent", "immediately", "now", "limited time"]):
#         score += 20
#         cons.append("Creates urgency pressure to rush decision")

#     # 🎁 REWARD TRAP
#     if any(word in t for word in ["win", "lottery", "prize", "reward"]):
#         score += 25
#         cons.append("Too-good-to-be-true reward offer")

#     # 🔐 SENSITIVE DATA REQUEST
#     if any(word in t for word in ["otp", "password", "pin", "verify account"]):
#         score += 30
#         cons.append("Requests sensitive confidential information")

#     # 🏦 IMPERSONATION
#     if any(word in t for word in ["bank", "rbi", "income tax", "police", "kyc"]):
#         score += 20
#         cons.append("Impersonates trusted authority or institution")

#     # 🔗 CLICK BAIT
#     if any(word in t for word in ["click here", "open link", "tap below"]):
#         score += 15
#         cons.append("Encourages clicking potentially unsafe links")

#     # ✅ SAFE SIGNALS
#     if "meeting" in t or "schedule" in t:
#         pros.append("Contains normal professional or neutral context")

#     if "thank you" in t or "regards" in t:
#         pros.append("Polite conversational tone")

#     if len(urls) == 0:
#         pros.append("No suspicious links detected")

#     pattern = "Scam Pattern" if score > 50 else "Possibly Safe"

#     return pros, cons, score, pattern


# def analyze_text(text):
#     start = time.time()

#     if not text.strip():
#         return jsonify({"error": "Empty input"}), 400

#     processed = clean_text(text)

#     proba = pipeline.predict_proba([processed])[0]
#     labels = list(pipeline.classes_)
#     scam_prob = proba[labels.index("scam")]

#     prediction = "scam" if scam_prob >= threshold else "safe"
#     trust_score = int((1 - scam_prob) * 100)

#     # 🔥 Rule-based analysis
#     pros, cons, rule_score, pattern = explain_scam(text)

#     combined_score = (100 - trust_score) + (rule_score or 0)

#     if combined_score > 80:
#         risk = "High Risk"
#     elif combined_score > 50:
#         risk = "Suspicious"
#     else:
#         risk = "Safe"

#     # ✅ SAVE TO DB
    
    
#     try:
#         print("CURRENT USER ID:", current_user.id)
#         scan = Scan(
#             text=text,
#             prediction=prediction,
#             risk=risk,
#             user_id=current_user.id
#         )
#         db.session.add(scan)
#         db.session.commit()
#     except Exception as e:
#         print("DB ERROR:", e)
#         db.session.rollback()

#     # 🔔 Notification
#     if prediction == "scam":
#         add_notification("🚨 Scam detected")

#     def generate_summary(risk):
#         if risk == "High Risk":
#             return "Strong scam indicators detected. Avoid interaction."
#         elif risk == "Suspicious":
#             return "Some warning signs detected. Proceed carefully."
#         else:
#             return "Appears mostly safe."

#     trust_score = max(0, min(100, trust_score))

#     return jsonify({
#         "prediction": prediction,
#         "confidence": round(scam_prob * 100, 2),
#         "trust_score": trust_score,
#         "risk": risk,
#         "pros": pros,
#         "cons": cons,
#         "pattern": pattern,
#         "summary": generate_summary(risk)
#     })


# # ---------------- STATS (PART 3 FIX) ---------------- #

# @app.route("/stats")
# def stats():
#     total = Scan.query.filter_by(user_id=current_user.id).count()

#     scam = Scan.query.filter_by(
#         user_id=current_user.id,
#         prediction="scam"
#     ).count()

#     safe = total - scam

#     recent = Scan.query.filter_by(
#         user_id=current_user.id
#     ).order_by(Scan.created_at.desc()).limit(10).all()

#     return jsonify({
#         "total": total,
#         "scam": scam,
#         "safe": safe,
#         "history": [
#             {
#                 "text": s.text[:50],
#                 "risk": s.risk,
#                 "time": s.created_at.strftime("%H:%M")
#             } for s in recent
#         ],

#         # 🔥 PART 3 ADDITION
#         "risk_distribution": {
#             "High Risk": Scan.query.filter_by(user_id=current_user.id, risk="High Risk").count(),
#             "Suspicious": Scan.query.filter_by(user_id=current_user.id, risk="Suspicious").count(),
#             "Safe": Scan.query.filter_by(user_id=current_user.id, risk="Safe").count()
#         }
#     })
    
# # @app.route("/admin/stats")
# # @login_required
# # @admin_required
# # def admin_stats():
# #     total_users = User.query.count()
# #     total_scans = Scan.query.count()

# #     scam = Scan.query.filter_by(prediction="scam").count()
# #     safe = total_scans - scam

# #     users = User.query.all()

# #     user_data = []

# #     for u in users:
# #         user_scans = Scan.query.filter_by(user_id=u.id).count()
# #         user_scam = Scan.query.filter_by(user_id=u.id, prediction="scam").count()

# #         user_data.append({
# #             "username": u.username,
# #             "total_scans": user_scans,
# #             "scam": user_scam,
# #             "safe": user_scans - user_scam
# #         })

# #     return jsonify({
# #         "total_users": total_users,
# #         "total_scans": total_scans,
# #         "scam": scam,
# #         "safe": safe,
# #         "users": user_data
# #     })
    
# # @app.route("/admin/user/<int:user_id>")
# # @login_required
# # @admin_required
# # def user_detail(user_id):
# #     scans = Scan.query.filter_by(user_id=user_id).all()

# #     history = [
# #         {
# #             "text": s.text[:40],
# #             "risk": s.risk,
# #             "time": s.created_at.strftime("%H:%M")
# #         }
# #         for s in scans
# #     ]

# #     return jsonify({
# #         "total": len(scans),
# #         "high_risk": len([s for s in scans if s.risk == "High Risk"]),
# #         "suspicious": len([s for s in scans if s.risk == "Suspicious"]),
# #         "safe": len([s for s in scans if s.risk == "Safe"]),
# #         "history": history
# #     })


# # ---------------- INIT ---------------- #

# if __name__ == "__main__":
#     with app.app_context():
#         db.create_all()

#     app.run(debug=True, port=5000)




from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import datetime
from flask import make_response
from reportlab.pdfgen import canvas
from io import BytesIO
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -----------------------------
# APP CONFIG
# -----------------------------
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
# ------------------------------
# UPLOAD FOLDER CONFIG
# ------------------------------

UPLOAD_FOLDER = "uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# DATABASE MODELS
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


class Scan(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    message = db.Column(db.Text)

    score = db.Column(db.Integer)

    level = db.Column(db.String(50))

    date = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow
    )

# -----------------------------
# CREATE DATABASE
# -----------------------------
with app.app_context():
    db.create_all()

# -----------------------------
# SCAM DETECTION LOGIC
# -----------------------------
def calculate_risk(message):

    message = message.lower()

    score = 0

    reasons = []

    # --------------------------------
    # KEYWORDS
    # --------------------------------

    high_risk_words = [
        "otp",
        "bank",
        "password",
        "account",
        "arrest",
        "cbi",
        "warrant",
        "urgent",
        "click",
        "verify",
        "digital arrest",
        "video call",
        "illegal",
        "parcel",
        "suspended",
        "job scam",
        "lottery"
    ]

    # --------------------------------
    # DETECT SCAM WORDS
    # --------------------------------

    for word in high_risk_words:

        if word in message:

            score += 15

            reasons.append(
                f"Suspicious keyword detected: {word}"
            )

    # --------------------------------
    # LIMIT SCORE
    # --------------------------------

    score = min(score, 100)

    # --------------------------------
    # RISK LEVEL
    # --------------------------------

    if score >= 70:

        level = "High Risk 🚨"

    elif score >= 40:

        level = "Medium Risk ⚠️"

    else:

        level = "Low Risk ✅"

    # --------------------------------
    # AI EXPLANATION
    # --------------------------------

    if score >= 70:

        explanation = """
This message shows strong scam indicators including urgency,
authority threats, phishing keywords, or financial fraud attempts.
Extreme caution is recommended.
"""

    elif score >= 40:

        explanation = """
This message contains suspicious patterns and may attempt
social engineering or phishing attacks.
Verify carefully before responding.
"""

    else:

        explanation = """
This message appears mostly safe and does not contain
major scam indicators.
"""

    # --------------------------------
    # RETURN VALUES
    # --------------------------------

    return score, level, reasons, explanation
# -----------------------------
# ROUTES
# -----------------------------

@app.route("/")
def home():
    return redirect("/login")

# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            return redirect("/scan")

        return "Invalid Username or Password ❌"

    return render_template("login.html")

# -----------------------------
# REGISTER
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            return "User already exists ❌"

        new_user = User(
            username=username,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

# -----------------------------
# SCAN PAGE
# -----------------------------
@app.route("/scan")
def scan():
    return render_template("scan.html")

# -----------------------------
# PREDICT
# -----------------------------
@app.route("/predict", methods=["POST"])
def predict():

    message = request.form.get("message", "")
    file = request.files.get("screenshot")

    # --------------------------------
    # CHECK BOTH EMPTY
    # --------------------------------

    if not message and not file:
        return "Please enter message or upload screenshot"


   # --------------------------------
# IMAGE ANALYSIS USING OCR
# --------------------------------

    if file and file.filename != "":

     filename = secure_filename(file.filename)

    upload_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )

    file.save(upload_path)

    # -----------------------------
    # EXTRACT TEXT FROM IMAGE
    # -----------------------------

    try:

        image = Image.open(upload_path)

        extracted_text = pytesseract.image_to_string(image)

        # Combine OCR text with manual message

        message = message + " " + extracted_text

    except Exception as e:

        print("OCR ERROR:", e)

    # --------------------------------
    # SCAM DETECTION
    # --------------------------------

    score, level, reasons, explanation = calculate_risk(message)

    # --------------------------------
    # SAVE TO DATABASE
    # --------------------------------

    new_scan = Scan(
        message=message,
        score=score,
        level=level
    )

    db.session.add(new_scan)
    db.session.commit()

    # --------------------------------
    # SHOW RESULT
    # --------------------------------

    return render_template(
        "result.html",
        message=message,
        score=score,
        level=level,
        reasons=reasons,
        explanation=explanation
    )

# -----------------------------
# DASHBOARD
# -----------------------------
# =========================================
# DASHBOARD ROUTE
# =========================================

@app.route("/dashboard")
def dashboard():

    # -------------------------
    # GET ALL SCANS
    # -------------------------

    scans = Scan.query.order_by(
        Scan.date.desc()
    ).all()

    # -------------------------
    # TOTAL COUNTS
    # -------------------------

    total = len(scans)

    high_risk = len([
        s for s in scans
        if "High" in s.level
    ])

    medium_risk = len([
        s for s in scans
        if "Medium" in s.level
    ])

    low_risk = len([
        s for s in scans
        if "Low" in s.level
    ])

    # -------------------------
    # RISK PERCENTAGES
    # -------------------------

    if total > 0:

        high_percent = round(
            (high_risk / total) * 100
        )

        medium_percent = round(
            (medium_risk / total) * 100
        )

        low_percent = round(
            (low_risk / total) * 100
        )

    else:

        high_percent = 0
        medium_percent = 0
        low_percent = 0

    # -------------------------
    # CATEGORY COUNTS
    # -------------------------

    otp_scams = 0
    banking_scams = 0
    arrest_scams = 0
    job_scams = 0
    link_scams = 0

    # -------------------------
    # AI THREAT ANALYSIS
    # -------------------------

    for scan in scans:

        msg = scan.message.lower()

        # OTP FRAUD

        if (
            "otp" in msg
            or "verification code" in msg
            or "one time password" in msg
        ):

            otp_scams += 1

        # BANKING SCAMS

        if (
            "bank" in msg
            or "account" in msg
            or "upi" in msg
            or "transaction" in msg
        ):

            banking_scams += 1

        # DIGITAL ARREST

        if (
            "digital arrest" in msg
            or "cbi" in msg
            or "police" in msg
            or "warrant" in msg
            or "court" in msg
            or "arrest" in msg
        ):

            arrest_scams += 1

        # JOB SCAMS

        if (
            "job" in msg
            or "interview" in msg
            or "salary" in msg
            or "recruitment" in msg
        ):

            job_scams += 1

        # LINK / PHISHING

        if (
            "http" in msg
            or "www" in msg
            or "click" in msg
            or "link" in msg
        ):

            link_scams += 1

    # -------------------------
    # LIVE THREAT SCORE
    # -------------------------

    threat_score = (
        (high_risk * 3)
        + (medium_risk * 2)
        + (low_risk * 1)
    )

    # -------------------------
    # RETURN TEMPLATE
    # -------------------------

    return render_template(

        "dashboard.html",

        # DATABASE
        scans=scans,

        # COUNTS
        total=total,

        high_risk=high_risk,
        medium_risk=medium_risk,
        low_risk=low_risk,

        # PERCENTAGES
        high_percent=high_percent,
        medium_percent=medium_percent,
        low_percent=low_percent,

        # CATEGORY DATA
        otp_scams=otp_scams,
        banking_scams=banking_scams,
        arrest_scams=arrest_scams,
        job_scams=job_scams,
        link_scams=link_scams,

        # AI THREAT
        threat_score=threat_score
    )
    
@app.route("/reports")
def reports():

    scans = Scan.query.order_by(Scan.date.desc()).all()

    high = len([s for s in scans if "High" in s.level])
    medium = len([s for s in scans if "Medium" in s.level])
    low = len([s for s in scans if "Low" in s.level])

    return render_template(
        "reports.html",
        scans=scans,
        high=high,
        medium=medium,
        low=low
    )
    
@app.route("/export_pdf")
def export_pdf():

    scans = Scan.query.order_by(
        Scan.date.desc()
    ).all()

    # -------------------------
    # CREATE PDF
    # -------------------------

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    # -------------------------
    # TITLE
    # -------------------------

    pdf.setFont("Helvetica-Bold", 20)

    pdf.drawString(
        180,
        800,
        "Scam Shield Report"
    )

    y = 750

    # -------------------------
    # ADD SCANS
    # -------------------------

    for scan in scans[:20]:

        pdf.setFont("Helvetica", 11)

        pdf.drawString(
            50,
            y,
            f"Message: {scan.message[:60]}"
        )

        pdf.drawString(
            50,
            y - 20,
            f"Risk Score: {scan.score}"
        )

        pdf.drawString(
            50,
            y - 40,
            f"Risk Level: {scan.level}"
        )

        y -= 80

        # NEW PAGE IF SPACE ENDS
        if y < 100:

            pdf.showPage()

            y = 750

    # -------------------------
    # SAVE PDF
    # -------------------------

    pdf.save()

    buffer.seek(0)

    # -------------------------
    # DOWNLOAD RESPONSE
    # -------------------------

    response = make_response(
        buffer.read()
    )

    response.headers[
        'Content-Type'
    ] = 'application/pdf'

    response.headers[
        'Content-Disposition'
    ] = \
        'attachment; filename=scam_report.pdf'

    return response
    
    
# =========================================
# LEARN PAGE
# =========================================

@app.route('/learn')
def learn():

    scam_categories = [

        {
            "title": "Digital Arrest Scam",
            "icon": "🚨",
            "risk": "Critical",

            "description":
            "Fraudsters impersonate police or CBI officers and threaten victims with fake arrest warrants.",

            "example":
            "Victim receives a video call claiming illegal parcels were found in their name.",

            "prevention":
            [
                "Never trust unknown officials on video calls",
                "Real police never demand money digitally",
                "Verify through official police helplines"
            ]
        },

        {
            "title": "OTP Scam",
            "icon": "💳",
            "risk": "High",

            "description":
            "Scammers trick users into sharing OTPs to steal bank money.",

            "example":
            "Fake bank executive asks for OTP to 'verify account'.",

            "prevention":
            [
                "Never share OTP with anyone",
                "Banks never ask for OTPs",
                "Enable SMS alerts"
            ]
        },

        {
            "title": "Job Scam",
            "icon": "💼",
            "risk": "High",

            "description":
            "Fake companies offer high-paying jobs and ask for registration fees.",

            "example":
            "User receives WhatsApp message promising ₹50,000 salary after paying ₹2,000 fee.",

            "prevention":
            [
                "Never pay for jobs",
                "Verify company websites",
                "Check LinkedIn/company presence"
            ]
        },

        {
            "title": "Phishing Link Scam",
            "icon": "🔗",
            "risk": "Medium",

            "description":
            "Fake websites steal passwords and banking details.",

            "example":
            "SMS says your bank account is blocked and asks you to click a link.",

            "prevention":
            [
                "Avoid suspicious links",
                "Check website URL carefully",
                "Enable two-factor authentication"
            ]
        },

        {
            "title": "Lottery Scam",
            "icon": "🎰",
            "risk": "Medium",

            "description":
            "Users are told they won a lottery and must pay fees to claim it.",

            "example":
            "Message says you won ₹25 lakh international lottery.",

            "prevention":
            [
                "Ignore unrealistic prizes",
                "Never pay processing fees",
                "Block suspicious contacts"
            ]
        }

    ]

    return render_template(
        'learn.html',
        scam_categories=scam_categories
    )


@app.route("/alerts")
def alerts():

    trending_scams = [
        {"name": "Digital Arrest Scam", "risk": 95},
        {"name": "Fake Job Scam", "risk": 80},
        {"name": "OTP Fraud", "risk": 92},
        {"name": "Lottery Scam", "risk": 70},
        {"name": "Fake Banking Alert", "risk": 88},
    ]

    return render_template(
        "alerts.html",
        trending_scams=trending_scams
    )

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)