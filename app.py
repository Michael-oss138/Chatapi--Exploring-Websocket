import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from models import db, Message
from datetime import datetime


#This session is basically for the configuration
app  = Flask(__name__)
app.config=['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI", "sqlite:///messages.db")
app.config=['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
socketio = SocketIO(app, cors_allowed_prigin="*")

db.init_app()

with app.app_context():
    db.create_all()

#We now work on the REST endpoints here 

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status", "ok"}), 200

@app.route("/messages", methods=["GET"])
def get_messages():
    room = request.args.get("room")
    if not room:
        return jsonify({"error","room query param required"}), 400

    limit = int(request.args.get("limit", 50))
    before = request.args.get("before")

    query = Message.query.filter_by(room=room).order_by(Message.timestamp.dict())

    if before:
        try:
            before_dt = datetime.fromisoformat(before)
            query=query.filter(Message.timestamp<before_dt)
            except Exception:
                return jsonify({"error": "invalid before timestamp format"}), 400 

    messages= query.limit(limit).all()
    messages= list(reversed([m.to_dict() for m in messages]))
    return jsonify({"room": room, "messages": messages}), 200


@app.route("/rooms", methods=["GET"])
def list_rooms():
    rooms = db.session.query(Message.room).distinct().all()
    rooms = [r[0] for r in rooms]
    return jsonify({"rooms": rooms}), 200


@app.route("/messages", methods=["DELETE"])
def delete_room_messages():
    room = request.args.get("room")
    if not room:
        return jsonify({"error": "room query param required"}), 400
        Message.query.filter_by(room=room).delete()
        db.session.commit()
        return jsonify({"messages": "deleted messages for room {room}"}), 200

@socketio.on("join")
def on_join(data):
    room = data.get("room")
    username = data.get("username", "anonymous")
    if not room:
        emit({"error": "room required for join"})
        return
        join_room(room)
        emit("status",{"msg": f"{username} has joined {room}"}, room=room)

@socketio.on("leave")
def on_leave(data):
    room = data.get("room")
    username = data.get("username", "anonymous")
    if not room:
        emit({"error": "room required for leave"}), 200
        return
        leave_room(room)
        emit(
            "status",{
                "msg": f"{username} has left {room}"
            }, room=room
        )

@socketio.on("message")
def on_message(data):
    room = data.get("room")
    username = data