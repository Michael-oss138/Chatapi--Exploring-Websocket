from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(50), nullable=True)
    password_hash = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password: str):
        self.password_hash = generate.password_hash(raw_password)


    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


    def to_dict(self):
        return{
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformar()
        }

class Message(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    room = db.Column(db.String(50), nullable= False, index= True)
    username = db.Column(db.String(100), nullable= False)
    body = db.Column(db.String(100), nullable= False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return{
            "id": self.id,
            "room": self.room,
            "username": self.username,
            "body": self.body,
            "timestamp": self.timestamp.isoformat()
        }