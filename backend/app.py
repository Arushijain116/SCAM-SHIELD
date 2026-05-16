from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

app.config["SECRET_KEY"] = "secret123"
app.config["CORS_HEADERS"] = "Content-Type"

CORS(app, supports_credentials=True)
import docx
from PyPDF2 import PdfReader

from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, pickle, time
import pytesseract
from PIL import Image

from models import db, User, Scan
from utils.preprocess import clean_text
from utils.url_blacklist import BLACKLIST
from functools import wraps







def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({"error": "Admin only"}), 403
        return f(*args, **kwargs)
    return decorated


# ---------------- CONFIG ---------------- #

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

db.init_app(app)

CORS(app,
     supports_credentials=True,
     origins=["http://127.0.0.1:5500","http://localhost:5500"])

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Unauthorized"}), 401

login_manager.login_view = "login"

app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=False,  # True only if HTTPS
    SESSION_COOKIE_HTTPONLY=True
)


# 🔥 Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 🔥 Load ML model
pipeline = pickle.load(open(os.path.join(BASE_DIR, "model", "pipeline.pkl"), "rb"))
threshold = float(open(os.path.join(BASE_DIR, "model", "threshold.txt")).read())

# ---------------- USER ---------------- #
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return "Backend running 🚀"

# ---------------- AUTH ---------------- #

@app.route("/register", methods=["POST"])
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)

    username = data.get("username", "").strip().lower()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "User exists"}), 400

    # 🔥 First user becomes admin automatically
    is_admin = User.query.count() == 0

    user = User(
        username=username,
        password=generate_password_hash(password),
        is_admin=is_admin
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registered"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)

    username = data.get("username", "").strip().lower()
    password = data.get("password", "").strip()

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"error": "User not found"}), 401

    if not check_password_hash(user.password, password):
        return jsonify({"error": "Wrong password"}), 401

    login_user(user, remember=False)
    return jsonify({"message": "Login successful"})
    

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/scan-file", methods=["POST"])
@login_required
def scan_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join("uploads", filename)

        os.makedirs("uploads", exist_ok=True)
        file.save(filepath)

        # 🔥 TEMP TEST (important)
        return jsonify({
            "risk": "Safe",
            "confidence": 90,
            "pros": ["File processed"],
            "cons": [],
            "text": "Test content"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out"})

# ---------------- ALERTS ---------------- #

@app.route("/alerts")
@login_required
def alerts():
    return jsonify([
        {
            "type": "Phishing",
            "message": "Fake bank login pages are targeting users",
            "level": "High"
        },
        {
            "type": "Lottery Scam",
            "message": "WhatsApp lottery scams increasing rapidly",
            "level": "Medium"
        },
        {
            "type": "KYC Fraud",
            "message": "Scammers posing as bank KYC agents",
            "level": "High"
        }
    ])
# ---------------- NOTIFICATIONS ---------------- #

notifications = {}

def add_notification(msg):
    user_id = current_user.id

    if user_id not in notifications:
        notifications[user_id] = []

    notifications[user_id].append({
        "msg": msg,
        "time": datetime.now().strftime("%H:%M:%S")
    })

@app.route("/notifications")
@login_required
def get_notifications():
    user_id = current_user.id
    return jsonify(notifications.get(user_id, [])[-5:])

# ---------------- SCAN ---------------- #

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    text = request.json.get("text", "")
    return analyze_text(text)

# ---------------- CORE ---------------- #

import re
from urllib.parse import urlparse

SHORTENERS = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "rb.gy"]

def extract_urls(text):
    return re.findall(r'(https?://\S+|www\.\S+)', text)

import socket

def analyze_url(url):
    parsed = urlparse(url if url.startswith("http") else "http://" + url)
    domain = parsed.netloc.lower()

    risk = 0
    reasons = []

    # 🔗 1. URL Shortener
    if any(short in domain for short in SHORTENERS):
        risk += 30
        reasons.append("Shortened URL detected (destination hidden)")

    # 🧠 2. Suspicious Keywords
    suspicious_keywords = ["login", "verify", "secure", "update", "bank", "account"]
    if any(k in url.lower() for k in suspicious_keywords):
        risk += 20
        reasons.append("Contains phishing-related keywords")

    # 🌐 3. Fake Domain Structure
    if domain.count('.') > 3:
        risk += 15
        reasons.append("Unusually complex domain structure")

    # 🔍 4. Hyphen Trick
    if "-" in domain:
        risk += 10
        reasons.append("Domain uses hyphen (common phishing trick)")

    # 🚨 5. IP Address Instead of Domain
    if re.match(r"\d+\.\d+\.\d+\.\d+", domain):
        risk += 25
        reasons.append("Uses IP address instead of domain name")

    # 🔌 6. Domain resolution check
    try:
        socket.gethostbyname(domain)
    except:
        risk += 20
        reasons.append("Domain does not resolve (suspicious)")
        
        # 🚨 7. Blacklist match
    if any(bad in url.lower() for bad in BLACKLIST):
     risk += 40
    reasons.append("URL matches known scam patterns database")
    
    # 🌐 8. Suspicious TLD
    if domain.endswith((".xyz", ".top", ".tk", ".ml")):
     risk += 20
    reasons.append("Uses suspicious top-level domain")

    return risk, reasons


def explain_scam(text):
    t = text.lower()

    pros = []
    cons = []
    score = 0

    # 🔗 URL ANALYSIS
    urls = extract_urls(text)
    for url in urls:
        url_risk, url_reasons = analyze_url(url)
        score += url_risk
        for r in url_reasons:
         cons.append(f"🔗 Link Risk: {r}")
         if urls:
           cons.append(f"Detected {len(urls)} link(s) in the message")

    # 📱 PHONE NUMBER DETECTION
    if re.search(r'\+?\d{10,}', text):
        score += 10
        cons.append("Contains phone number (common in scam outreach)")

    # 🚨 URGENCY
    if any(word in t for word in ["urgent", "immediately", "now", "limited time"]):
        score += 20
        cons.append("Creates urgency pressure to rush decision")

    # 🎁 REWARD TRAP
    if any(word in t for word in ["win", "lottery", "prize", "reward"]):
        score += 25
        cons.append("Too-good-to-be-true reward offer")

    # 🔐 SENSITIVE DATA REQUEST
    if any(word in t for word in ["otp", "password", "pin", "verify account"]):
        score += 30
        cons.append("Requests sensitive confidential information")

    # 🏦 IMPERSONATION
    if any(word in t for word in ["bank", "rbi", "income tax", "police", "kyc"]):
        score += 20
        cons.append("Impersonates trusted authority or institution")

    # 🔗 CLICK BAIT
    if any(word in t for word in ["click here", "open link", "tap below"]):
        score += 15
        cons.append("Encourages clicking potentially unsafe links")

    # ✅ SAFE SIGNALS
    if "meeting" in t or "schedule" in t:
        pros.append("Contains normal professional or neutral context")

    if "thank you" in t or "regards" in t:
        pros.append("Polite conversational tone")

    if len(urls) == 0:
        pros.append("No suspicious links detected")

    pattern = "Scam Pattern" if score > 50 else "Possibly Safe"

    return pros, cons, score, pattern


def analyze_text(text):
    start = time.time()

    if not text.strip():
        return jsonify({"error": "Empty input"}), 400

    processed = clean_text(text)

    proba = pipeline.predict_proba([processed])[0]
    labels = list(pipeline.classes_)
    scam_prob = proba[labels.index("scam")]

    prediction = "scam" if scam_prob >= threshold else "safe"
    trust_score = int((1 - scam_prob) * 100)

    # 🔥 Rule-based analysis
    pros, cons, rule_score, pattern = explain_scam(text)

    combined_score = (100 - trust_score) + (rule_score or 0)

    if combined_score > 80:
        risk = "High Risk"
    elif combined_score > 50:
        risk = "Suspicious"
    else:
        risk = "Safe"

    # ✅ SAVE TO DB
    
    
    try:
        print("CURRENT USER ID:", current_user.id)
        scan = Scan(
            text=text,
            prediction=prediction,
            risk=risk,
            user_id=current_user.id
        )
        db.session.add(scan)
        db.session.commit()
    except Exception as e:
        print("DB ERROR:", e)
        db.session.rollback()

    # 🔔 Notification
    if prediction == "scam":
        add_notification("🚨 Scam detected")

    def generate_summary(risk):
        if risk == "High Risk":
            return "Strong scam indicators detected. Avoid interaction."
        elif risk == "Suspicious":
            return "Some warning signs detected. Proceed carefully."
        else:
            return "Appears mostly safe."

    trust_score = max(0, min(100, trust_score))

    return jsonify({
        "prediction": prediction,
        "confidence": round(scam_prob * 100, 2),
        "trust_score": trust_score,
        "risk": risk,
        "pros": pros,
        "cons": cons,
        "pattern": pattern,
        "summary": generate_summary(risk)
    })


# ---------------- STATS (PART 3 FIX) ---------------- #

@app.route("/stats")
@login_required
def stats():
    total = Scan.query.filter_by(user_id=current_user.id).count()

    scam = Scan.query.filter_by(
        user_id=current_user.id,
        prediction="scam"
    ).count()

    safe = total - scam

    recent = Scan.query.filter_by(
        user_id=current_user.id
    ).order_by(Scan.created_at.desc()).limit(10).all()

    return jsonify({
        "total": total,
        "scam": scam,
        "safe": safe,
        "history": [
            {
                "text": s.text[:50],
                "risk": s.risk,
                "time": s.created_at.strftime("%H:%M")
            } for s in recent
        ],

        # 🔥 PART 3 ADDITION
        "risk_distribution": {
            "High Risk": Scan.query.filter_by(user_id=current_user.id, risk="High Risk").count(),
            "Suspicious": Scan.query.filter_by(user_id=current_user.id, risk="Suspicious").count(),
            "Safe": Scan.query.filter_by(user_id=current_user.id, risk="Safe").count()
        }
    })
    
    @app.route("/admin/stats")
    @login_required
    @admin_required
    def admin_stats():
     total_users = User.query.count()
    total_scans = Scan.query.count()

    scam = Scan.query.filter_by(prediction="scam").count()
    safe = total_scans - scam

    users = User.query.all()

    user_data = []

    for u in users:
        user_scans = Scan.query.filter_by(user_id=u.id).count()
        user_scam = Scan.query.filter_by(user_id=u.id, prediction="scam").count()

        user_data.append({
            "username": u.username,
            "total_scans": user_scans,
            "scam": user_scam,
            "safe": user_scans - user_scam
        })

    return jsonify({
        "total_users": total_users,
        "total_scans": total_scans,
        "scam": scam,
        "safe": safe,
        "users": user_data
    })
    
    @app.route("/admin/user/<int:user_id>")
    @login_required
    @admin_required
    def user_detail(user_id):
      scans = Scan.query.filter_by(user_id=user_id).all()

    history = [
        {
            "text": s.text[:40],
            "risk": s.risk,
            "time": s.created_at.strftime("%H:%M")
        }
        for s in scans
    ]

    return jsonify({
        "total": len(scans),
        "high_risk": len([s for s in scans if s.risk == "High Risk"]),
        "suspicious": len([s for s in scans if s.risk == "Suspicious"]),
        "safe": len([s for s in scans if s.risk == "Safe"]),
        "history": history
    })


# ---------------- INIT ---------------- #

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)