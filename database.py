"""
PostgreSQL Database Models
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    referral_code = db.Column(db.String(10), unique=True, nullable=False)
    referred_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    gmail_accounts = db.relationship('GmailAccount', backref='user', lazy=True, cascade='all, delete-orphan')
    earnings = db.relationship('Earnings', backref='user', lazy=True, cascade='all, delete-orphan')
    withdrawals = db.relationship('Withdrawal', backref='user', lazy=True, cascade='all, delete-orphan')

class GmailAccount(db.Model):
    __tablename__ = 'gmail_accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    recovery_email = db.Column(db.String(120), nullable=True)
    password = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='pending')  # pending, verified, rejected
    price = db.Column(db.Float, default=5.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.String(36), nullable=True)
    
    earnings = db.relationship('Earnings', backref='gmail_account', lazy=True, cascade='all, delete-orphan')

class Earnings(db.Model):
    __tablename__ = 'earnings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'sales', 'referral'
    gmail_id = db.Column(db.String(36), db.ForeignKey('gmail_accounts.id'), nullable=True)
    status = db.Column(db.String(50), default='pending')  # pending, approved, withdrawn
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
