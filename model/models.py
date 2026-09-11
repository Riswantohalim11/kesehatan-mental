from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class BaseModel(db.Model):
    __abstract__ = True
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)

class User(BaseModel, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(20), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    test_results = db.relationship('TestResult', backref='user', cascade='all, delete-orphan', lazy=True)
    chats = db.relationship('ChatHistory', backref='user', cascade='all, delete-orphan', lazy=True)
    emotions = db.relationship('EmotionResult', backref='user', cascade='all, delete-orphan', lazy=True)
    bookings = db.relationship('Booking', backref='user', cascade='all, delete-orphan', lazy=True)
    bookmarks = db.relationship('Bookmark', backref='user', cascade='all, delete-orphan', lazy=True)
    articles = db.relationship('Article', backref='author', cascade='all, delete-orphan', lazy=True)

class MentalTest(BaseModel):
    __tablename__ = 'mental_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False) # 'Stres', 'Kecemasan', 'Depresi'
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TestResult(BaseModel):
    __tablename__ = 'test_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    test_category = db.Column(db.String(50), nullable=False) # 'Skrining Awal', 'Stres', 'Kecemasan', 'Depresi'
    score = db.Column(db.Integer, nullable=False)
    category_result = db.Column(db.String(100), nullable=False) # Ringkasan indikasi kondisi emosional
    description = db.Column(db.Text, nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    risk_level = db.Column(db.String(50), nullable=True, default='Rendah') # 'Rendah', 'Sedang', 'Tinggi'
    risk_response = db.Column(db.String(150), nullable=True) # Respon pertanyaan keselamatan
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatHistory(BaseModel):
    __tablename__ = 'chat_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    sender = db.Column(db.String(10), nullable=False) # 'user' or 'bot'
    message = db.Column(db.Text, nullable=False)
    emotion_label = db.Column(db.String(50), nullable=True)
    emotion_confidence = db.Column(db.Float, nullable=True)
    topic_label = db.Column(db.String(50), nullable=True) # Topic Tracking
    is_crisis = db.Column(db.Boolean, nullable=False, default=False)
    session_id = db.Column(db.String(50), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    emotion_details = db.relationship('EmotionResult', backref='chat', cascade='all, delete-orphan', lazy=True)

class EmotionResult(BaseModel):
    __tablename__ = 'emotion_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat_history.id', ondelete='CASCADE'), nullable=True)
    emotion_label = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Category(BaseModel):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    articles = db.relationship('Article', backref='category', cascade='all, delete-orphan', lazy=True)

class Article(BaseModel):
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Service(BaseModel):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    contact = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False) # 'Psikolog', 'Konselor', 'Hotline Darurat'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='service', cascade='all, delete-orphan', lazy=True)

class Booking(BaseModel):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    booking_time = db.Column(db.String(20), nullable=True, default='09:00 WIB')
    complaint = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending') # 'Pending', 'Approved', 'Cancelled'
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Quote(BaseModel):
    __tablename__ = 'quotes'
    
    id = db.Column(db.Integer, primary_key=True)
    quote = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False, default='Anonim')
    tips = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bookmark(BaseModel):
    __tablename__ = 'bookmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Establish unique constraints
    __table_args__ = (db.UniqueConstraint('user_id', 'article_id', name='user_article_bookmark'),)
    
    article = db.relationship('Article')

class ContactSetting(BaseModel):
    __tablename__ = 'contact_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    email_support = db.Column(db.String(100), nullable=False, default='support@mindhaven.id')
    whatsapp_number = db.Column(db.String(50), nullable=False, default='+62 812-3456-7890')
    office_address = db.Column(db.Text, nullable=False, default='Gedung MindHaven Care Center Lt. 3, Jl. Jend. Sudirman No. 108, Jakarta Selatan')
    google_maps_url = db.Column(db.Text, nullable=False, default='https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3966.27361957262!2d106.8202!3d-6.2146!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e69f3e46c764e57%3A0x6b1427f8eb2be289!2sJl.%20Jend.%20Sudirman%2C%20Jakarta%20Selatan!5e0!3m2!1sid!2sid!4v1700000000000!5m2!1sid!2sid')
    operating_hours = db.Column(db.String(150), nullable=False, default='Senin – Sabtu: 08.00 – 17.00 WIB')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContactMessage(BaseModel):
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Unread')
    admin_reply = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='contact_messages', lazy=True)

