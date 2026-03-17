from flask import Blueprint, request, jsonify
from ..models import db, Assignment, StudyGroupMembership,AssignmentResult, Deck, StudyGroup, User
from datetime import datetime
from sqlalchemy import func

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
        deck_id=data.get('deck_id'),
        mode=data.get('mode'),
        score=data.get('score', 0),
        total=data.get('total', 0),
        completed_at=datetime.utcnow()
    )
    db.session.add(result)
    db.session.commit()
    return jsonify({'message': 'Result submitted', 'result_id': result.id}), 201

@tests_bp.route('/assignments/<int:assignment_id>/results', methods=['GET'])
def get_assignment_results(assignment_id):
    """Get all results for an assignment (teacher view)"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    results = AssignmentResult.query.filter_by(assignment_id=assignment_id).all()
    
    result_list = []
    for r in results:
        user = User.query.get(r.user_id)
        result_list.append({
            'id': r.id,
            'user_id': r.user_id,
            'username': user.username if user else 'Unknown',
            'deck_id': r.deck_id,
            'deck_name': r.deck_name if hasattr(r, 'deck_name') else (Deck.query.get(r.deck_id).name if r.deck_id and Deck.query.get(r.deck_id) else None),
            'mode': r.mode,
            'score': r.score,
            'total': r.total,
            'completed_at': r.completed_at.isoformat() if hasattr(r, 'completed_at') and r.completed_at else None
        })
    
    return jsonify(result_list)

@tests_bp.route('/assignments/<int:assignment_id>/results/<int:user_id>', methods=['GET'])
def get_user_assignment_results(assignment_id, user_id):
    """Get results for a specific user in an assignment"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    results = AssignmentResult.query.filter_by(
        assignment_id=assignment_id,
        user_id=user_id
    ).all()
    
    result_list = []
    for r in results:
        user = User.query.get(r.user_id)
        result_list.append({
            'id': r.id,
            'user_id': r.user_id,
            'username': user.username if user else 'Unknown',
            'deck_id': r.deck_id,
            'deck_name': r.deck_name if hasattr(r, 'deck_name') else (Deck.query.get(r.deck_id).name if r.deck_id and Deck.query.get(r.deck_id) else None),
            'mode': r.mode,
            'score': r.score,
            'total': r.total,
            'completed_at': r.completed_at.isoformat() if hasattr(r, 'completed_at') and r.completed_at else None
        })
    
    return jsonify(result_list)

@tests_bp.route('/assignments/<int:assignment_id>/leaderboard', methods=['GET'])
def assignment_leaderboard(assignment_id):
    """Get leaderboard for an assignment"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    results = db.session.query(
        AssignmentResult.user_id,
        func.sum(AssignmentResult.score).label('total_score'),
        func.sum(AssignmentResult.total).label('total_possible'),
        func.count(AssignmentResult.id).label('attempt_count')
    ).filter(
        AssignmentResult.assignment_id == assignment_id
    ).group_by(
        AssignmentResult.user_id
    ).all()
    
    leaderboard = []
    for r in results:
        user = User.query.get(r.user_id)
        avg_score = (r.total_score * 100.0 / r.total_possible) if r.total_possible else 0
        leaderboard.append({
            'user_id': r.user_id,
            'username': user.username if user else 'Unknown',
            'avg_score': round(avg_score, 2),
            'total_score': r.total_score,
            'total_possible': r.total_possible,
            'attempt_count': r.attempt_count
        })
    
    # Sort by average score descending
    leaderboard.sort(key=lambda x: x['avg_score'], reverse=True)
    
    return jsonify(leaderboard)

@tests_bp.route('/groups/<int:group_id>/leaderboard', methods=['GET'])
def group_leaderboard(group_id):
    """Get leaderboard for a group"""
    group = StudyGroup.query.get_or_404(group_id)
    
    results = db.session.query(
        AssignmentResult.user_id,
        func.avg((AssignmentResult.score * 100.0 / AssignmentResult.total)).label('avg_score'),
        func.count(AssignmentResult.id).label('attempt_count')
    ).join(
        Assignment, AssignmentResult.assignment_id == Assignment.id
    ).filter(
        Assignment.group_id == group_id
    ).group_by(
        AssignmentResult.user_id
    ).all()
    
    leaderboard = []
    for r in results:
        user = User.query.get(r.user_id)
        leaderboard.append({
            'user_id': r.user_id,
            'username': user.username if user else 'Unknown',
            'avg_score': round(r.avg_score, 2) if r.avg_score else 0,
            'attempt_count': r.attempt_count
        })
    
    # Sort by average score descending
    leaderboard.sort(key=lambda x: x['avg_score'], reverse=True)
    
    return jsonify(leaderboard)

@tests_bp.route('/assignments/<int:assignment_id>/statistics', methods=['GET'])
def assignment_statistics(assignment_id):
    """Get detailed statistics for an assignment"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    results = AssignmentResult.query.filter_by(assignment_id=assignment_id).all()
    
    if not results:
        return jsonify({
            'total_attempts': 0,
            'total_unique_students': 0,
            'average_score': 0,
            'highest_score': 0,
            'lowest_score': 0,
            'pass_rate': 0,
            'by_mode': {},
            'by_deck': {}
        })
    
    # Calculate basic stats
    scores = [(r.score / r.total * 100) if r.total > 0 else 0 for r in results]
    
    stats = {
        'total_attempts': len(results),
        'total_unique_students': len(set(r.user_id for r in results)),
        'average_score': round(sum(scores) / len(scores), 2) if scores else 0,
        'highest_score': round(max(scores), 2) if scores else 0,
        'lowest_score': round(min(scores), 2) if scores else 0,
        'pass_rate': round(len([s for s in scores if s >= 50]) / len(scores) * 100, 2) if scores else 0,
        'by_mode': {},
        'by_deck': {}
    }
    
    # Group by mode
    modes = {}
    for r in results:
        mode = r.mode or 'Unknown'
        if mode not in modes:
            modes[mode] = {'scores': [], 'count': 0, 'total_score': 0, 'total_max': 0}
        score_percent = (r.score / r.total * 100) if r.total > 0 else 0
        modes[mode]['scores'].append(score_percent)
        modes[mode]['count'] += 1
        modes[mode]['total_score'] += r.score
        modes[mode]['total_max'] += r.total
    
    for mode, data in modes.items():
        stats['by_mode'][mode] = {
            'count': data['count'],
            'avg_score': round(sum(data['scores']) / len(data['scores']), 2) if data['scores'] else 0,
            'total_score': data['total_score'],
            'total_max': data['total_max']
        }
    
    # Group by deck
    decks = {}
    for r in results:
        deck_name = r.deck_name or f"Deck {r.deck_id}" or 'All Decks'
        if deck_name not in decks:
            decks[deck_name] = {'scores': [], 'count': 0, 'total_score': 0, 'total_max': 0}
        score_percent = (r.score / r.total * 100) if r.total > 0 else 0
        decks[deck_name]['scores'].append(score_percent)
        decks[deck_name]['count'] += 1
        decks[deck_name]['total_score'] += r.score
        decks[deck_name]['total_max'] += r.total
    
    for deck, data in decks.items():
        stats['by_deck'][deck] = {
            'count': data['count'],
            'avg_score': round(sum(data['scores']) / len(data['scores']), 2) if data['scores'] else 0,
            'total_score': data['total_score'],
            'total_max': data['total_max']
        }
    
    return jsonify(stats)

@tests_bp.route('/assignments/<int:assignment_id>/group-status', methods=['GET'])
def get_assignment_group_status(assignment_id):
    """Get assignment status for all group members"""
    a = Assignment.query.get_or_404(assignment_id)
    group = StudyGroup.query.get_or_404(a.group_id)
    
    # Get all group members
    memberships = StudyGroupMembership.query.filter_by(group_id=a.group_id).all()
    group_members = []
    for m in memberships:
        user = User.query.get(m.user_id)
        if user:
            group_members.append({
                'id': user.id,
                'username': user.username,
                'name': user.name if hasattr(user, 'name') else None,
                'email': user.email
            })
    
    # Get all results for this assignment
    results = AssignmentResult.query.filter_by(assignment_id=assignment_id).all()
    user_results = {}
    for r in results:
        if r.user_id not in user_results:
            user_results[r.user_id] = []
        user_results[r.user_id].append({
            'deck_id': r.deck_id,
            'deck_name': Deck.query.get(r.deck_id).name if r.deck_id else None,
            'mode': r.mode,
            'score': r.score,
            'total': r.total,
            'completed_at': r.completed_at.isoformat() if r.completed_at else None,
            'passed': (r.score / r.total * 100) >= 50 if r.total > 0 else False
        })
    
    # Build status for each group member
    status_data = {
        'group_id': a.group_id,
        'assignment_id': assignment_id,
        'group_members': group_members,
        'not_taken': [],
        'not_passed': [],
        'passed': []
    }
    
    for member in group_members:
        if member['id'] not in user_results:
            # Student hasn't taken the test
            status_data['not_taken'].append(member)
        else:
            # Student has taken the test, check if they passed
            member_results = user_results[member['id']]
            all_passed = all(r['passed'] for r in member_results)
            if all_passed:
                status_data['passed'].append({
                    'member': member,
                    'results': member_results
                })
            else:
                status_data['not_passed'].append({
                    'member': member,
                    'results': member_results
                })
    
    return jsonify(status_data)