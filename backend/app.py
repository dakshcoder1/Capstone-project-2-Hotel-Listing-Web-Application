from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
from models import db, User, Hotel, Reviews
from auth import hash_password, verify_password, create_token, get_current_user, get_admin_user
import json 
app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db.init_app(app)
# db = SQLAlchemy(app)


# class Hotel(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(200), nullable=False)
#     location = db.Column(db.String(200))
#     is_veg = db.Column(db.Boolean, nullable=False)
#     prices = db.Column(db.Integer)
#     images = db.Column(db.Text)  # Store multiple image URLs as comma separated
#     contact_no = db.Column(db.String(200))
#     description = db.Column(db.Text)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
#     is_admin = db.Column(db.Boolean, default=False)  # NEW: Admin flag
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     reviews = db.relationship(
#         "Reviews",
#         backref="hotel",
#         cascade="all, delete",
#         lazy=True
#     )

#     def to_dict(self):
#         return {
#             'id': self.id,
#             'name': self.name,
#             'location': self.location,
#             'is_veg': self.is_veg,
#             'prices': self.prices,
#             'images': self.images.split(',') if self.images else [],
#             'contact_no': self.contact_no,
#             'description': self.description,
#             'user_id': self.user_id,
#             "is_admin": self.is_admin,
#             'created_at': self.created_at.isoformat() if self.created_at else None,
#         }
    
# class Reviews(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username=db.Column(db.String(200),nullable=False)
#     hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
#     comment = db.Column(db.Text)
#     rating =db.Column(db.Float)
#     is_admin = db.Column(db.Boolean, default=False)  # NEW: Admin flag
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)


    
#     def to_dict(self):  # Convert model to dictionary for JSON response
#         return {
#             'id': self.id,
#             'username':self.username,
#             'hotel_id': self.hotel_id,
#             'comment': self.comment,
#             'rating': self.rating,
#             'created_at':self.created_at,
#         }
    
# class User(db.Model):
#     __tablename__ = 'users'

#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password_hash = db.Column(db.String(256), nullable=False)
#     is_admin = db.Column(db.Boolean, default=False)
#     hotels = db.relationship('Hotel', backref='owner', lazy=True)


# def to_dict_with_stats(self):
#     return {
#         "id": self.id,
#         "username": self.username,
#         "email": self.email,
#         "is_admin": self.is_admin,
#         "total_hotels": len(self.hotels)
#     }



# @app.route('/')
# def index():
#     return jsonify({
#         "success": True,
#         "message": "REST API is running",
#         "endpoints": {
#             "hotels": "/api/hotels",
#         }
#     })


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route("/reviews")
def review_page():
    return render_template("review.html")


@app.route("/hotel/<int:id>")
def hotel_detail(id):
    return render_template("hotel-detailed.html", hotel_id=id)


@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    existing = User.query.filter_by(username=username).first()
    if existing:
        return jsonify({"error": "Username already exists"}), 400

    hashed = hash_password(password)

    user = User(
        username=username,
        email=email,
        password_hash=hashed,
        role="user"
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not verify_password(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(user.id, user.role)

    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    }), 200


@app.route('/api/hotels', methods=['GET'])
def get_hotels():

    hotels = Hotel.query.all()

    return jsonify({
        'success': True,
        'count': len(hotels),
        'hotels': [hotel.to_dict() for hotel in hotels]
    }), 200


# GET /api/books/<id> - Get single book
@app.route('/api/hotels/<int:id>', methods=['GET'])
def get_hotel(id):
    hotel = db.session.get(Hotel, id)

    if not hotel:
        return jsonify({
            'success': False,
            'error': 'Hotel not found'
        }), 404  # Return 404 status code

    return jsonify({
        'success': True,
        'hotel': hotel.to_dict()
        
    })
# POST /api/books - Create new book
@app.route('/api/hotels', methods=['POST'])
def add_hotels():

    # ✅ Check login
    current_user, error = get_current_user()
    if error:
        return error
    
    if current_user.role not in ["admin", "user"]:
        return jsonify({"error": "Only users or admins can add hotels"}), 403
    
    
    user_id = current_user.id

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    raw_images = data.get('images', [])
    clean_images = []

    # 🔥 Clean & normalize images
    for img in raw_images:
        if isinstance(img, str):

            parts = img.replace(",", "\n").split("\n")

            for part in parts:
                part = part.strip().replace('"', '')

                if part and part not in ["1", "null", "undefined"]:
                    clean_images.append(part)

    # 🚀 Create Hotel AFTER cleaning
    new_hotel = Hotel(
        name=data.get('name'),
        location=data.get('location'),
        is_veg=data.get('is_veg'),
        prices=data.get('prices'),
        images=json.dumps(clean_images),
        contact_no=data.get('contact_no'),
        description=data.get('description'),
        user_id=current_user.id
          )

    db.session.add(new_hotel)
    db.session.commit()

    return jsonify({
        'success': True,
        'hotel': new_hotel.to_dict()
    }), 201


@app.route('/api/hotels/<int:id>', methods=['PUT'])
def update_hotel(id):

    current_user, error = get_current_user()
    if error:
        return error

    if current_user.role == "guest":
        return jsonify({"error": "Guests cannot edit hotels"}), 403

    hotel = Hotel.query.get_or_404(id)

    user_id = current_user.id

    if hotel.user_id != user_id and current_user.role != "admin":
        return jsonify({"msg": "Not allowed"}), 403

    data = request.get_json()

    if 'menu_card' in data:
        hotel.menu_card = data['menu_card']

    hotel.name = data.get('name', hotel.name)
    hotel.location = data.get('location', hotel.location)
    hotel.is_veg = data.get('is_veg', hotel.is_veg)
    hotel.prices = data.get('prices', hotel.prices)
    hotel.contact_no = data.get('contact_no', hotel.contact_no)
    hotel.description = data.get('description', hotel.description)

    if 'images' in data:
        raw_images = data.get('images', [])
        clean_images = []

        for img in raw_images:
            if isinstance(img, str):
                parts = img.replace(",", "\n").split("\n")
                for part in parts:
                    part = part.strip().replace('"', '')
                    if part:
                        clean_images.append(part)

        hotel.images = json.dumps(clean_images)

    db.session.commit()

    return jsonify({
        'success': True,
        'hotel': hotel.to_dict()
    })


# DELETE /api/books/<id> - Delete book
@app.route('/api/hotels/<int:id>', methods=['DELETE'])
def delete_hotel(id):

    # 🔐 Check if user is logged in
    current_user, error = get_current_user()
    if error:
        return error

    # ❌ Guests cannot delete
    if current_user.role == "guest":
        return jsonify({"error": "Guests cannot delete hotels"}), 403

    # 🔍 Find hotel
    hotel = Hotel.query.get_or_404(id)

    # 🚫 Only owner OR admin can delete
    if hotel.user_id != current_user.id and current_user.role != "admin":
      return jsonify({"error": "Unauthorized"}), 403
    # 🗑 Delete hotel
    db.session.delete(hotel)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Hotel deleted successfully"
    }), 200

# GET REVIEWS OF A HOTEL
@app.route("/api/hotels/<int:id>/reviews", methods=["GET"])
def get_reviews(id):
    # Step 1: Check if user is logged in
    current_user, error = get_current_user()
    if error:
        return error

    hotel = db.session.get(Hotel, id)

    if not hotel:
        return jsonify({"success": False, "error": "Hotel not found"}), 404

    return jsonify({
        "success": True,
        "reviews": [review.to_dict() for review in hotel.reviews]
    })


# ADD REVIEW TO HOTEL
@app.route("/api/hotels/<int:id>/reviews", methods=["POST"])
def add_review(id):
    # Step 1: Check if user is logged in
    current_user, error = get_current_user()
    if error:
        return error

    hotel = db.session.get(Hotel, id)

    if not hotel:
        return jsonify({"success": False, "error": "Hotel not found"}), 404

    data = request.get_json()

    if not data or not data.get("username") or not data.get("rating"):
        return jsonify({"success": False, "error": "Username and rating required"}), 400

    review = Reviews(
        username=data["username"],
        rating=data["rating"],
        comment=data.get("comment"),
        hotel_id=id
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({"success": True, "review": review.to_dict()}), 201


# DELETE REVIEW
@app.route("/api/reviews/<int:id>", methods=["DELETE"])
def delete_review(id):
    # Step 1: Check if user is logged in
    current_user, error = get_current_user()
    if error:
        return error

    review = db.session.get(Reviews, id)

    if not review:
        return jsonify({"success": False, "error": "Review not found"}), 404

    db.session.delete(review)
    db.session.commit()

    return jsonify({"success": True, "message": "Review deleted"})


def init_db():
    with app.app_context():
        db.create_all()

        if Hotel.query.count() == 0:
            sample_hotels = [
                Hotel(name='Sunrise',  location='Gorakpur',is_veg=True, prices=8000),
                Hotel(name='Funplay', location='Jalna',is_veg=True, prices=18000),
                Hotel(name='Master',  location='Delhi',is_veg=True, prices=2000),
            ]
            db.session.add_all(sample_hotels)
            db.session.commit()
            print('Sample hotels added!')
 


@app.route('/api/hotels/<int:id>/details', methods=['GET'])
def get_hotel_details(id):
    # Step 1: Check if user is logged in
    current_user, error = get_current_user()
    if error:
        return error

    hotel = db.session.get(Hotel, id)

    if not hotel:
        return jsonify({
            'success': False,
            'error': 'Hotel not found'
        }), 404

    # Get all reviews of this hotel
    reviews = Reviews.query.filter_by(hotel_id=id).all()

    # Calculate average rating
    if reviews:
        avg_rating = sum(r.rating for r in reviews if r.rating) / len(reviews)
    else:
        avg_rating = 0

    return jsonify({
        'success': True,
        'hotel': hotel.to_dict(),
        'reviews': [review.to_dict() for review in reviews],
        'average_rating': round(avg_rating, 1),
        'total_reviews': len(reviews)
    })
@app.route('/api/hotels/<int:id>/full', methods=['GET'])
def get_full_details(id):
    
    hotel = db.session.get(Hotel, id)

    if not hotel:
        return jsonify({'success': False}), 404

    reviews = hotel.reviews

    avg_rating = round(
        sum(r.rating for r in reviews if r.rating) / len(reviews),
        1
    ) if reviews else 0

    return jsonify({
        'success': True,
        'hotel': {
            **hotel.to_dict(),
            'average_rating': avg_rating
        },
        'reviews': [r.to_dict() for r in reviews]
    })




@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    # Step 1: Check if user is logged in AND is admin
    current_user, error = get_admin_user()
    if error:
        return error  # Returns 401 if not logged in, 403 if not admin

    # Step 2: Get all users
    users = User.query.all()
    return jsonify({'users': [user.to_dict_with_stats() for user in users]})


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):

    current_user, error = get_admin_user()
    if error:
        return error

    # 🚫 Prevent admin deleting himself
    if current_user.id == user_id:
        return jsonify({"error": "You cannot delete your own account"}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"})


@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    current_user, error = get_admin_user()
    if error:
        return error

    total_users = User.query.count()
    total_hotels = Hotel.query.count()

    # Fix reviews crash
    
    total_reviews = 0

    return jsonify({
        'total_users': total_users,
        'total_hotels': total_hotels,
        'total_reviews': total_reviews
    })

@app.route('/api/admin/hotels', methods=['GET'])
def get_all_hotels_admin():

    current_user, error = get_admin_user()
    if error:
        return error

    hotels = Hotel.query.all()
    result = []

    for hotel in hotels:

        hotel_data = hotel.to_dict()

        owner = User.query.get(hotel.user_id)

        if owner:
            hotel_data["username"] = owner.username
        else:
            hotel_data["username"] = "Unknown"

        result.append(hotel_data)

    return jsonify({"hotels": result})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)