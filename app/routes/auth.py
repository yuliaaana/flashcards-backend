from flask import Blueprint, request, jsonify
from app.models import User, Folder, Deck
from app import bcrypt, db

bp = Blueprint('auth', __name__, url_prefix='/api')

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        folders = Folder.query.filter_by(user_id=user.id).all()
        decks = Deck.query.filter_by(user_id=user.id).all()

        folder_list = [folder.to_dict() for folder in folders]
        deck_list = [
            {
                "id": deck.id,
                "name": deck.name,
                "creator": deck.creator,  
                "terms": deck.terms,     
                "folder_id": deck.folder_id,
                "created_at": deck.created_at
            }
            for deck in decks
        ]

        return jsonify({
            "message": "Login successful",
            "redirect_url": "/dashboard",
            "user_id": user.id,
            "role": user.role,
            "folders": folder_list,
            "decks": deck_list
        }), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({"message": "All fields are required"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"message": "Username or email already exists"}), 409

    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    print(password_hash)
    new_user = User(username=username, email=email, password_hash=password_hash)

    db.session.add(new_user)
    
    db.session.commit()
    print(new_user.id)
    
    return jsonify({
        "message": "User registered successfully!",
        "user_id": new_user.id,
        "redirect_url": "/homepage"
    }), 201

