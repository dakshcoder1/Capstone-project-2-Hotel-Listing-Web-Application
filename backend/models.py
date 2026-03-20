from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    is_veg = db.Column(db.Boolean, nullable=False)
    prices = db.Column(db.Integer)
    images = db.Column(db.Text)
    contact_no = db.Column(db.String(200))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    menu_card = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviews = db.relationship(
        "Reviews",
        backref="hotel",
        cascade="all, delete",
        lazy=True
    )

    # ✅ MOVE THIS INSIDE CLASS
    def to_dict(self):

        image_list = []

        if self.images:
            try:
                image_list = json.loads(self.images)
            except:
                image_list = [img.strip() for img in self.images.split(",") if img.strip()]

        clean_images = []

        for img in image_list:
            if isinstance(img, str):
                img = img.strip()
                if (
                    img
                    and img not in ["1", "null", "undefined"]
                    and not img.startswith("data:image/jpeg;base64:1")
                    and (
                        img.startswith("http://")
                        or img.startswith("https://")
                        or img.startswith("data:image")
                    )
                ):
                    clean_images.append(img)

        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "is_veg": self.is_veg,
            "price": self.prices,
            "images": clean_images,
            "contact_no": self.contact_no,
            "description": self.description,
            "user_id": self.user_id,
            "menu_card": self.menu_card,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
class Reviews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(200),nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    comment = db.Column(db.Text)
    rating =db.Column(db.Float)
    is_admin = db.Column(db.Boolean, default=False)  # NEW: Admin flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    
    def to_dict(self):  # Convert model to dictionary for JSON response
        return {
            'id': self.id,
            'username':self.username,
            'hotel_id': self.hotel_id,
            'comment': self.comment,
            'rating': self.rating,
            'created_at':self.created_at,
        }
    
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    hotels = db.relationship('Hotel', backref='user', lazy=True)

    def to_dict_with_stats(self):
        
        total_hotels = Hotel.query.filter_by(user_id=self.id).count()

        return {
        "id": self.id,
        "username": self.username,
        "email": self.email,
        "is_admin": self.role == "admin",
        "total_todos": total_hotels,
        "completed_todos": total_hotels,
        "created_at": self.created_at.isoformat() if self.created_at else None
    }