from datetime import datetime
from sqlalchemy import JSON
from .db import db

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    user = db.relationship('User', backref='conversations')
    messages = db.relationship('Message', back_populates='conversation', order_by='Message.timestamp')

    @property
    def last_message(self):
        """Get the last message in the conversation"""
        return self.messages[-1] if self.messages else None

    def add_message(self, content: str, role: str, metadata: dict = None):
        """Add a new message to the conversation"""
        message = Message(
            conversation_id=self.id,
            content=content,
            role=role,
            message_metadata=metadata or {}
        )
        db.session.add(message)
        return message

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(50))  # 'user' or 'assistant'
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Changed from JSONB to JSON
    message_metadata = db.Column(JSON, default=dict)
    
    # Relationship
    conversation = db.relationship('Conversation', back_populates='messages') 