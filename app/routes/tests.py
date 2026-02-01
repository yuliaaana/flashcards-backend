from flask import Blueprint, request, jsonify
from ..models import db, TestAssignment, TestResult, Deck, StudyGroup, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

tests_bp = Blueprint('tests', __name__)

@tests_bp.route('/assignments', methods=['POST'])
@jwt_required()
def assign_test():
    data = request.json
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.role != 'teacher':
        return jsonify({'error': 'Only teachers can assign tests'}), 403
    assignment = TestAssignment(
        test_id=data['test_id'],
        group_id=data.get('group_id'),
        student_id=data.get('student_id'),
        assigned_by=user_id,
        due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify({'message': 'Test assigned', 'assignment_id': assignment.id}), 201

@tests_bp.route('/assignments/<int:assignment_id>/submit', methods=['POST'])
@jwt_required()
def submit_test(assignment_id):
    user_id = get_jwt_identity()
    data = request.json
    assignment = TestAssignment.query.get_or_404(assignment_id)
    if assignment.student_id and assignment.student_id != user_id:
        return jsonify({'error': 'Not allowed'}), 403
    result = TestResult(
        assignment_id=assignment_id,
        student_id=user_id,
        score=data['score']
    )
    db.session.add(result)
    db.session.commit()
    return jsonify({'message': 'Test submitted', 'result_id': result.id}), 201

@tests_bp.route('/assignments/<int:assignment_id>/results', methods=['GET'])
@jwt_required()
def get_assignment_results(assignment_id):
    user_id = get_jwt_identity()
    assignment = TestAssignment.query.get_or_404(assignment_id)
    user = User.query.get(user_id)
    if user.role != 'teacher' and assignment.student_id != user_id:
        return jsonify({'error': 'Not allowed'}), 403
    results = TestResult.query.filter_by(assignment_id=assignment_id).all()
    return jsonify([
        {'student_id': r.student_id, 'score': r.score, 'submitted_at': r.submitted_at.isoformat()} for r in results
    ])

@tests_bp.route('/groups/<int:group_id>/leaderboard', methods=['GET'])
@jwt_required()
def group_leaderboard(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    results = db.session.query(TestResult.student_id, db.func.avg(TestResult.score).label('avg_score'))\
        .join(TestAssignment, TestResult.assignment_id == TestAssignment.id)\
        .filter(TestAssignment.group_id == group_id)\
        .group_by(TestResult.student_id)\
        .order_by(db.desc('avg_score')).all()
    leaderboard = [{'student_id': r.student_id, 'avg_score': r.avg_score} for r in results]
    return jsonify(leaderboard)
