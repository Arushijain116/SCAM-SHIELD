from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# 👤 User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)

# 📊 Scan History Model
class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    prediction = db.Column(db.String(10))
    risk = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 🔥 MUST EXIST
    created_at = db.Column(db.DateTime, default=datetime.utcnow)