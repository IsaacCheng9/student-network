import os
import sqlite3
from datetime import datetime

from flask import Flask, request, session
from flask_socketio import SocketIO

from src.views.achievements import achievements_blueprint
from src.views.chat import chat_blueprint
from src.views.connections import connections_blueprint
from src.views.login import login_blueprint
from src.views.posts import posts_blueprint
from src.views.profile import profile_blueprint
from src.views.quizzes import quizzes_blueprint
from src.views.staff import staff_blueprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")
app = Flask(__name__)
socketio = SocketIO(app)
app.register_blueprint(achievements_blueprint, url_prefix="")
app.register_blueprint(chat_blueprint, url_prefix="")
app.register_blueprint(connections_blueprint, url_prefix="")
app.register_blueprint(login_blueprint, url_prefix="")
app.register_blueprint(posts_blueprint, url_prefix="")
app.register_blueprint(profile_blueprint, url_prefix="")
app.register_blueprint(quizzes_blueprint, url_prefix="")
app.register_blueprint(staff_blueprint, url_prefix="")
app.secret_key = ("\xfd{H\xe5 <\x95\xf9\xe3\x96.5\xd1\x01O <!\xd5\""
                  "xa2\xa0\x9fR\xa1\xa8")
app.url_map.strict_slashes = False
users = {}


@socketio.on("username", namespace="/private")
def receive_username(username):
    users[username] = request.sid


@socketio.on("private_message", namespace="/private")
def private_message(payload):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()

        now = datetime.now()

        cur.execute("INSERT INTO PrivateMessages "
                    "(sender, receiver, message, date) VALUES (?, ?, ?, ?);",
                    (session["username"], payload["username"],
                     payload["message"], now.strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()

    if payload["username"] in users:
        recipient_session_id = users[payload['username']]

        socketio.emit('new_private_message', payload,
                      room=recipient_session_id, namespace="/private")
    # user is not online at the moment
    else:
        pass


if __name__ == "__main__":
    app.run(debug=True)
