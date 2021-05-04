from flask import Blueprint, render_template

from src.helper import *

chat_blueprint = Blueprint("chat", __name__,
                           static_folder="static",
                           template_folder="templates")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")


@chat_blueprint.route("/chat")
def chat():
    chat_rooms = get_all_connections(session["username"])
    chat_rooms = list(
        map(lambda x: (x[0], get_profile_picture(x[0])), chat_rooms))

    return render_template("chat.html",
                           requestCount=get_connection_request_count(),
                           username=session["username"],
                           rooms=chat_rooms, showChat=False)


@chat_blueprint.route("/chat/<username>")
def chat_username(username):
    chat_rooms = get_all_connections(session["username"])
    chat_rooms = list(
        map(lambda x: (x[0], get_profile_picture(x[0])), chat_rooms))

    '''with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT sender, receiver, message FROM "
            "PrivateMessages WHERE (sender=? OR receiver=?);", (session[
            "username"], username))'''

    return render_template("chat.html",
                           requestCount=get_connection_request_count(),
                           username=session["username"],
                           rooms=chat_rooms, showChat=True, room=username)
