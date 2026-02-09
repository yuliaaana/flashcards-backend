import base64
from flask import Blueprint, jsonify
from app.models import User, Folder, Deck
import os

bp = Blueprint('user', __name__, url_prefix='/api')

@bp.route('/user-data/<int:user_id>', methods=['GET'])
def get_user_data(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    folders = Folder.query.filter_by(user_id=user_id).all()
    decks = Deck.query.filter_by(user_id=user_id).all()

    folder_list = [folder.to_dict() for folder in folders]
    deck_list = [
        {
            "id": deck.id,
            "name": deck.name,
            "creator": deck.user.username, 
            "terms": deck.terms,     
            "folder_id": deck.folder_id,
            "created_at": deck.created_at.strftime("%d.%m.%Y"),
            "is_public": deck.is_public
        }
        for deck in decks
    ]

    avatar_base64 = None
    if user.avatar:
        try:
            avatar_base64 = base64.b64encode(user.avatar).decode('utf-8') 
        except Exception as e:
            print("Error encoding avatar:", e)
            avatar_base64 = None

    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": avatar_base64,
        "role": user.role
    }

    return jsonify({
        "user": user_data,
        "folders": folder_list,
        "decks": deck_list
    }), 200
