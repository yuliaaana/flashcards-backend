from flask import Blueprint, request, jsonify
from app import db
from app.models import StudyGroup, StudyGroupMembership, User

bp = Blueprint('groups', __name__, url_prefix='/api')

@bp.route('/groups', methods=['GET'])
def list_groups():
    teacher_id = request.args.get('teacher_id')
    query = StudyGroup.query
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    groups = query.all()
    result = []
    for group in groups:
        members = [m.user_id for m in group.memberships]
        result.append({
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "teacher_id": group.teacher_id,
            "members": members
        })
    return jsonify(result)

@bp.route('/groups', methods=['POST'])
def create_group():
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    user = User.query.get(teacher_id)
    if not user or user.role != 'teacher':
        return jsonify({"error": "Only teachers can create groups"}), 403
    group = StudyGroup(
        name=data['name'],
        description=data.get('description'),
        teacher_id=teacher_id
    )
    db.session.add(group)
    db.session.commit()
    return jsonify({"message": "Group created", "group_id": group.id}), 201

@bp.route('/groups/<int:group_id>/join', methods=['POST'])
def join_group(group_id):
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    membership = StudyGroupMembership.query.filter_by(group_id=group_id, user_id=user_id).first()
    if membership:
        return jsonify({"error": "Already a member"}), 400
    membership = StudyGroupMembership(group_id=group_id, user_id=user_id)
    db.session.add(membership)
    db.session.commit()
    return jsonify({"message": "Joined group"}), 200

@bp.route('/groups/<int:group_id>/leave', methods=['POST'])
def leave_group(group_id):
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    membership = StudyGroupMembership.query.filter_by(group_id=group_id, user_id=user_id).first()
    if not membership:
        return jsonify({"error": "Not a member"}), 400
    db.session.delete(membership)
    db.session.commit()
    return jsonify({"message": "Left group"}), 200

@bp.route('/groups/<int:group_id>', methods=['GET'])
def get_group(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    members = [m.user_id for m in group.memberships]
    return jsonify({
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "teacher_id": group.teacher_id,
        "members": members
    })
