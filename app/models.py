from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.LargeBinary, nullable=True)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'teacher'

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship('User', backref=db.backref('folders', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at
            
        }

class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    creator = db.Column(db.String(255), nullable=False)  
    terms = db.Column(db.Integer, default=0)  
    is_public = db.Column(db.Boolean, default=False)  # <-- додано
    latest_test_result = db.Column(db.Float, nullable=True)  # Store percentage result as float
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship('User', backref=db.backref('decks', lazy=True))
    folder = db.relationship('Folder', backref=db.backref('decks', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "creator": self.user.username,
            "creator_id": self.user.id,    
            "terms": self.terms,
            "is_public": self.is_public,
            "latest_test_result": self.latest_test_result,
            "created_at": self.created_at.strftime("%d.%m.%Y")
        }


class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id'), nullable=False)
    front_title = db.Column(db.String(255), nullable=False)
    back_title = db.Column(db.String(255), nullable=False)
    back_description = db.Column(db.Text, nullable=True)  
    image_url = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_reviewed = db.Column(db.DateTime, nullable=True)
    review_count = db.Column(db.Integer, default=0)
    confidence_level = db.Column(db.Integer, default=0) 
    next_review = db.Column(db.DateTime, nullable=True)  
    
    
    deck = db.relationship('Deck', backref=db.backref('flashcards', lazy=True))
    

    def to_dict(self):
        return {
            "id": self.id,
            "deck_id": self.deck_id,
            "front_title": self.front_title,
            "back_title": self.back_title,
            "back_description": self.back_description,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "last_reviewed": self.last_reviewed,
            "review_count": self.review_count,
            "confidence_level": self.confidence_level,
            "next_review": self.next_review  
        }


# --- Study Groups and Test Assignment Models ---
class StudyGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='teaching_groups')

class StudyGroupMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    group = db.relationship('StudyGroup', backref=db.backref('memberships', lazy=True))
    user = db.relationship('User', backref=db.backref('group_memberships', lazy=True))

class StudyGroupDeck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id'), nullable=False)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    group = db.relationship('StudyGroup', backref=db.backref('group_decks', lazy=True))
    deck = db.relationship('Deck', backref=db.backref('group_links', lazy=True))
    adder = db.relationship('User', foreign_keys=[added_by])

class StudyGroupFolder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    group = db.relationship('StudyGroup', backref=db.backref('group_folders', lazy=True))
    folder = db.relationship('Folder', backref=db.backref('group_links', lazy=True))
    adder = db.relationship('User', foreign_keys=[added_by])

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    one_time_only = db.Column(db.Boolean, default=False)  # If True, students can only take the test once
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    group = db.relationship('StudyGroup', backref=db.backref('assignments', lazy=True))
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_assignments')
    decks = db.relationship('AssignmentDeck', backref='assignment', lazy=True, cascade='all, delete-orphan')
    modes = db.relationship('AssignmentMode', backref='assignment', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('AssignmentResult', backref='assignment', lazy=True, cascade='all, delete-orphan')

class AssignmentDeck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id'), nullable=False)
    deck = db.relationship('Deck')

class AssignmentMode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    mode = db.Column(db.String(50), nullable=False)  # 'flashcards', 'match', 'written', 'test'

class AssignmentResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id'), nullable=False)
    mode = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    completed_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship('User', backref=db.backref('assignment_results', lazy=True))
    deck = db.relationship('Deck')
    