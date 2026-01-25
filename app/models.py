from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.LargeBinary, nullable=True)

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
    