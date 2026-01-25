from flask import Blueprint, request, jsonify
from app import db
from app.models import Deck, Flashcard

bp = Blueprint('deck', __name__, url_prefix='/api')

@bp.route('/deck/<int:deck_id>/test-result', methods=['POST'])
def update_deck_test_result(deck_id):
    data = request.get_json()
    print('Received data:', data)
    result = data.get('test_result')
    if result is None:
        return jsonify({"message": "Missing test_result in request body"}), 400
    if not isinstance(result, (int, float, str)):
        return jsonify({"message": "test_result must be a number or string"}), 400
    try:
        result_float = float(result)
    except Exception:
        return jsonify({"message": "test_result could not be converted to float"}), 400
    deck = Deck.query.get(deck_id)
    if not deck:
        return jsonify({"message": "Deck not found"}), 404
    try:
        deck.latest_test_result = result_float
        db.session.commit()
        return jsonify({"message": "Test result updated", "deck": deck.to_dict()}), 200
    except Exception as e:
        import traceback
        print('Exception occurred:', str(e))
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"message": f"Error updating test result: {str(e)}"}), 500

@bp.route('/deck/<int:deck_id>', methods=['GET'])
def get_deck(deck_id):
    print(deck_id)
    deck = Deck.query.get(deck_id)

    if not deck:
        return jsonify({"message": "Deck not found"}), 404

    flashcards = Flashcard.query.filter_by(deck_id=deck.id).all()

    print(deck.to_dict())

    return jsonify({
        "deck": deck.to_dict(),
        "flashcards": [card.to_dict() for card in flashcards] 
    }), 200
