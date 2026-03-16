from flask import Blueprint, request, jsonify, current_app
from .. import db
from ..models import StudyGroup, StudyGroupMembership, StudyGroupDeck, StudyGroupFolder, User, Deck, Folder, Assignment, AssignmentDeck, AssignmentMode, AssignmentResult

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

@bp.route('/groups/user/<int:user_id>', methods=['GET'])
def get_user_groups(user_id):
    memberships = StudyGroupMembership.query.filter_by(user_id=user_id).all()
    group_ids = [m.group_id for m in memberships]
    groups = StudyGroup.query.filter(StudyGroup.id.in_(group_ids)).all()
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

# Endpoint for teachers to add students by nickname to a study group
@bp.route('/groups/<int:group_id>/add_students', methods=['POST'])
def add_students_to_group(group_id):
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    usernames = data.get('usernames', [])
    if not teacher_id or not usernames:
        return jsonify({"error": "teacher_id and usernames required"}), 400
    group = StudyGroup.query.get_or_404(group_id)
    if group.teacher_id != teacher_id:
        return jsonify({"error": "Only the group's teacher can add students"}), 403
    added = []
    added_emails = []
    not_found = []
    already_member = []
    for username in usernames:
        user = User.query.filter_by(username=username).first()
        if not user:
            not_found.append(username)
            continue
        membership = StudyGroupMembership.query.filter_by(group_id=group_id, user_id=user.id).first()
        if membership:
            already_member.append(username)
            continue
        membership = StudyGroupMembership(group_id=group_id, user_id=user.id)
        db.session.add(membership)
        added.append(username)
        added_emails.append(user.email)
    db.session.commit()
    return jsonify({
        "added": added,
        "added_emails": added_emails,
        "not_found": not_found,
        "already_member": already_member
    }), 200

# --- Attach / detach decks ---

@bp.route('/groups/<int:group_id>/decks', methods=['GET'])
def get_group_decks(group_id):
    StudyGroup.query.get_or_404(group_id)
    links = StudyGroupDeck.query.filter_by(group_id=group_id).all()
    result = []
    for link in links:
        deck = Deck.query.get(link.deck_id)
        if deck:
            result.append(deck.to_dict())
    return jsonify(result)

@bp.route('/groups/<int:group_id>/decks', methods=['POST'])
def add_deck_to_group(group_id):
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    deck_id = data.get('deck_id')
    if not teacher_id or not deck_id:
        return jsonify({"error": "teacher_id and deck_id required"}), 400
    group = StudyGroup.query.get_or_404(group_id)
    if group.teacher_id != teacher_id:
        return jsonify({"error": "Only the group's teacher can attach decks"}), 403
    deck = Deck.query.get(deck_id)
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    existing = StudyGroupDeck.query.filter_by(group_id=group_id, deck_id=deck_id).first()
    if existing:
        return jsonify({"error": "Deck already attached to this group"}), 400
    link = StudyGroupDeck(group_id=group_id, deck_id=deck_id, added_by=teacher_id)
    db.session.add(link)
    db.session.commit()
    return jsonify({"message": "Deck attached to group"}), 201

@bp.route('/groups/<int:group_id>/decks/<int:deck_id>', methods=['DELETE'])
def remove_deck_from_group(group_id, deck_id):
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    if not teacher_id:
        return jsonify({"error": "teacher_id required"}), 400
    group = StudyGroup.query.get_or_404(group_id)
    if group.teacher_id != teacher_id:
        return jsonify({"error": "Only the group's teacher can detach decks"}), 403
    link = StudyGroupDeck.query.filter_by(group_id=group_id, deck_id=deck_id).first()
    if not link:
        return jsonify({"error": "Deck not attached to this group"}), 404
    db.session.delete(link)
    db.session.commit()
    return jsonify({"message": "Deck removed from group"}), 200

# --- Attach / detach folders ---

@bp.route('/groups/<int:group_id>/folders', methods=['GET'])
def get_group_folders(group_id):
    StudyGroup.query.get_or_404(group_id)
    links = StudyGroupFolder.query.filter_by(group_id=group_id).all()
    result = []
    for link in links:
        folder = Folder.query.get(link.folder_id)
        if folder:
            result.append(folder.to_dict())
    return jsonify(result)

@bp.route('/groups/<int:group_id>/folders', methods=['POST'])
def add_folder_to_group(group_id):
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    folder_id = data.get('folder_id')
    if not teacher_id or not folder_id:
        return jsonify({"error": "teacher_id and folder_id required"}), 400
    group = StudyGroup.query.get_or_404(group_id)
    if group.teacher_id != teacher_id:
        return jsonify({"error": "Only the group's teacher can attach folders"}), 403
    folder = Folder.query.get(folder_id)
    if not folder:
        return jsonify({"error": "Folder not found"}), 404
    existing = StudyGroupFolder.query.filter_by(group_id=group_id, folder_id=folder_id).first()
    if existing:
        return jsonify({"error": "Folder already attached to this group"}), 400
    link = StudyGroupFolder(group_id=group_id, folder_id=folder_id, added_by=teacher_id)
    db.session.add(link)
    db.session.commit()
    return jsonify({"message": "Folder attached to group"}), 201

@bp.route('/groups/<int:group_id>/folders/<int:folder_id>', methods=['DELETE'])
def remove_folder_from_group(group_id, folder_id):
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    if not teacher_id:
        return jsonify({"error": "teacher_id required"}), 400
    group = StudyGroup.query.get_or_404(group_id)
    if group.teacher_id != teacher_id:
        return jsonify({"error": "Only the group's teacher can detach folders"}), 403
    link = StudyGroupFolder.query.filter_by(group_id=group_id, folder_id=folder_id).first()
    if not link:
        return jsonify({"error": "Folder not attached to this group"}), 404
    db.session.delete(link)
    db.session.commit()
    return jsonify({"message": "Folder removed from group"}), 200

# --- Assignments ---

from datetime import datetime

@bp.route('/groups/<int:group_id>/assignments', methods=['POST'])
def create_assignment(group_id):
    data = request.get_json()
    print(data)
    current_app.logger.info(f"Assignment data: {data}")
    teacher_id = data.get('teacher_id')
    title = data.get('title')
    description = data.get('description')
    due_date_str = data.get('due_date')  # ISO format, e.g. "2026-03-01T23:59:00"
    one_time_only = data.get('one_time_only', False)  # Default to False
    deck_ids = data.get('deck_ids', [])
    modes = data.get('modes', [])  # e.g. ["flashcards", "match", "test"]

    if not teacher_id or not title:
        return jsonify({"error": "teacher_id and title required"}), 400

    group = StudyGroup.query.get_or_404(group_id)
    if group.teacher_id != teacher_id:
        return jsonify({"error": "Only the group's teacher can create assignments"}), 403

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str)
        except ValueError:
            return jsonify({"error": "Invalid due_date format, use ISO format"}), 400

    assignment = Assignment(
        group_id=group_id,
        title=title,
        description=description,
        created_by=teacher_id,
        due_date=due_date,
        one_time_only=one_time_only
    )
    db.session.add(assignment)
    db.session.flush()  # get assignment.id before committing

    for deck_id in deck_ids:
        deck = Deck.query.get(deck_id)
        if not deck:
            db.session.rollback()
            return jsonify({"error": f"Deck {deck_id} not found"}), 404
        db.session.add(AssignmentDeck(assignment_id=assignment.id, deck_id=deck_id))

    for mode in modes:
        db.session.add(AssignmentMode(assignment_id=assignment.id, mode=mode))

    db.session.commit()
    return jsonify({"message": "Assignment created", "assignment_id": assignment.id}), 201

@bp.route('/groups/<int:group_id>/assignments', methods=['GET'])
def get_group_assignments(group_id):
    StudyGroup.query.get_or_404(group_id)
    assignments = Assignment.query.filter_by(group_id=group_id).order_by(Assignment.created_at.desc()).all()
    result = []
    for a in assignments:
        result.append({
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "group_id": a.group_id,
            "created_by": a.created_by,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "one_time_only": a.one_time_only,
            "deck_ids": [ad.deck_id for ad in a.decks],
            "modes": [am.mode for am in a.modes]
        })
    return jsonify(result)

@bp.route('/assignments/<int:assignment_id>', methods=['GET'])
def get_assignment(assignment_id):
    a = Assignment.query.get_or_404(assignment_id)
    decks_info = []
    for ad in a.decks:
        deck = Deck.query.get(ad.deck_id)
        if deck:
            decks_info.append(deck.to_dict())
    return jsonify({
        "id": a.id,
        "title": a.title,
        "description": a.description,
        "group_id": a.group_id,
        "created_by": a.created_by,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "due_date": a.due_date.isoformat() if a.due_date else None,
        "one_time_only": a.one_time_only,
        "decks": decks_info,
        "modes": [am.mode for am in a.modes]
    })

@bp.route('/assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    if not teacher_id:
        return jsonify({"error": "teacher_id required"}), 400
    a = Assignment.query.get_or_404(assignment_id)
    group = StudyGroup.query.get(a.group_id)
    if not group or group.teacher_id != teacher_id:
        return jsonify({"error": "Only the group's teacher can delete assignments"}), 403
    db.session.delete(a)
    db.session.commit()
    return jsonify({"message": "Assignment deleted"}), 200

@bp.route('/assignments/<int:assignment_id>/results', methods=['POST'])
def submit_assignment_result(assignment_id):
    data = request.get_json()
    user_id = data.get('user_id')
    deck_id = data.get('deck_id')
    mode = data.get('mode')
    score = data.get('score')
    total = data.get('total')

    if not all([user_id, deck_id, mode, score is not None, total is not None]):
        return jsonify({"error": "user_id, deck_id, mode, score, and total required"}), 400

    assignment = Assignment.query.get_or_404(assignment_id)

    # Check if one_time_only and user has already submitted for this assignment and deck
    if assignment.one_time_only:
        existing_result = AssignmentResult.query.filter_by(
            assignment_id=assignment_id,
            user_id=user_id,
            deck_id=deck_id
        ).first()
        if existing_result:
            return jsonify({"error": "You can only submit this assignment once per deck"}), 400

    result = AssignmentResult(
        assignment_id=assignment_id,
        user_id=user_id,
        deck_id=deck_id,
        mode=mode,
        score=score,
        total=total
    )
    db.session.add(result)
    db.session.commit()
    return jsonify({"message": "Result submitted", "result_id": result.id}), 201

@bp.route('/assignments/<int:assignment_id>/results', methods=['GET'])
def get_assignment_results(assignment_id):
    Assignment.query.get_or_404(assignment_id)
    results = AssignmentResult.query.filter_by(assignment_id=assignment_id).order_by(AssignmentResult.completed_at.desc()).all()
    output = []
    for r in results:
        user = User.query.get(r.user_id)
        deck = Deck.query.get(r.deck_id)
        output.append({
            "id": r.id,
            "user_id": r.user_id,
            "username": user.username if user else None,
            "deck_id": r.deck_id,
            "deck_name": deck.name if deck else None,
            "mode": r.mode,
            "score": r.score,
            "total": r.total,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None
        })
    return jsonify(output)

@bp.route('/assignments/<int:assignment_id>/results/<int:user_id>', methods=['GET'])
def get_student_assignment_results(assignment_id, user_id):
    Assignment.query.get_or_404(assignment_id)
    results = AssignmentResult.query.filter_by(assignment_id=assignment_id, user_id=user_id).order_by(AssignmentResult.completed_at.desc()).all()
    output = []
    for r in results:
        deck = Deck.query.get(r.deck_id)
        output.append({
            "id": r.id,
            "deck_id": r.deck_id,
            "deck_name": deck.name if deck else None,
            "mode": r.mode,
            "score": r.score,
            "total": r.total,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None
        })
    return jsonify(output)
