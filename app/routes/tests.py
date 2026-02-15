from flask import Blueprint, request, jsonify
from ..models import db, Assignment, AssignmentResult, Deck, StudyGroup, User
from datetime import datetime

tests_bp = Blueprint('tests', __name__, url_prefix='/api')

@tests_bp.route('/assignments/<int:assignment_id>/submit', methods=['POST'])
def submit_test(assignment_id):
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
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
