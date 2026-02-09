from flask import Blueprint, request, jsonify
from ..models import db, Assignment, AssignmentResult, Deck, StudyGroup, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

tests_bp = Blueprint('tests', __name__)

@tests_bp.route('/assignments/<int:assignment_id>/submit', methods=['POST'])
@jwt_required()
def submit_test(assignment_id):
    user_id = get_jwt_identity()
    data = request.json
    Assignment.query.get_or_404(assignment_id)
    result = AssignmentResult(
        assignment_id=assignment_id,
        user_id=user_id,
        deck_id=data['deck_id'],
        mode=data['mode'],
        score=data['score'],
        total=data['total']
    )
    db.session.add(result)
    db.session.commit()
    return jsonify({'message': 'Result submitted', 'result_id': result.id}), 201

@tests_bp.route('/groups/<int:group_id>/leaderboard', methods=['GET'])
@jwt_required()
def group_leaderboard(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    results = db.session.query(
        AssignmentResult.user_id,
        db.func.avg(AssignmentResult.score / AssignmentResult.total * 100).label('avg_score')
    )\
        .join(Assignment, AssignmentResult.assignment_id == Assignment.id)\
        .filter(Assignment.group_id == group_id)\
        .group_by(AssignmentResult.user_id)\
        .order_by(db.desc('avg_score')).all()
    leaderboard = []
    for r in results:
        user = User.query.get(r.user_id)
        leaderboard.append({
            'user_id': r.user_id,
            'username': user.username if user else None,
            'avg_score': round(r.avg_score, 2)
        })
    return jsonify(leaderboard)
