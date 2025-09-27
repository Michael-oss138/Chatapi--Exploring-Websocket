from flask_sqlalchemy import SQLALCHEMY 
from datetime import datetime

db = SQLALCHEMY()

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