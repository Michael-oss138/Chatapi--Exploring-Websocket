import os
import jwt
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from models import db, Message, User
from datetime import datetime, timedelta


#This session is basically for the configuration
app  = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI", "sqlite:///messages.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

JWT_SECRET = os.getenv("JWT_SECRET", "iammerge")

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

db.init_app(app)

with app.app_context():
    db.create_all()


#JWt sessoin.

def create_token(username= str, hours_valid: int = 1) -> str:
    payload = {
        "username": username, 
        "exp": datetime.utcnow() + timedelta(hours=hours_valid), 
        "iat": datetime.utcnow()
        }


    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token.decode("utf-8") if isinstance(token, bytes) else token

def decode_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithm=["HS256"])

#We now work on the REST endpoints here 

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/messages", methods=["GET"])
def get_messages():
    room = request.args.get("room")
    if not room:
        return jsonify({"error": "room query param required"}), 400

    limit = int(request.args.get("limit", 50))
    before = request.args.get("before")

    query = Message.query.filter_by(room=room).order_by(Message.timestamp.desc())

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
#Authentication here.

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    if not username or not email or not password:
        return jsonify({"error": "username, email and password required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "user is already taken"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 400

    user = User(username=username, email=email, full_name=full_name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "user created", "user": user.to_dict()}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid Credentials"}), 401

    token = create_token(user.username)
    return jsonify({"token": token, "user": user.to_dict()}), 200
        
#We now configure the sockets events here

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
    emit("status",{"msg": f"{username} has left {room}"}, room=room)

@socketio.on("message")
def on_message(data):
    room = data.get("room") 
    username = data.get("username", "anonymous")
    body = data.get("body")
    if not room or not body:
        emit(

            "error",{
                "error", "room and body are required"
            }
        )

        return
    msg = Message(username=username, body=body, room=room)
    db.session.add(msg)
    db.session.commit()

    payload={
        "id": msg.id,
        "room": room,
        "username": username,
        "body": body,
        "timestamp": msg.timestamp.isoformat()
    }
    emit("message", payload, room=room)


@socketio.on("disconnect")
def on_disconnect():
    print("client disconnected")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

