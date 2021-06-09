"""
Handles the view for the chat system and related functionality.
"""
import os

import student_network.helpers.helper_connections as helper_connections
import student_network.helpers.helper_general as helper_general
import student_network.helpers.helper_profile as helper_profile
from flask import Blueprint, render_template
from flask import session

chat_blueprint = Blueprint(
    "chat", __name__, static_folder="static", template_folder="templates"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")


@chat_blueprint.route("/chat")
def chat():
    chat_rooms = helper_general.get_all_connections(session["username"])
    chat_rooms = list(
        map(lambda x: (x[0], helper_profile.get_profile_picture(x[0])), chat_rooms)
    )

    chat_rooms = [list(x) for x in chat_rooms]
    
    for i, room in enumerate(chat_rooms):
        message = helper_general.get_messages(room[0], True)
        chat_rooms[i].append(message)
    
    actives = [x for x in chat_rooms if x[2][2] != ""]
    inactives = [x for x in chat_rooms if x[2][2] == ""]
    actives.sort(key=lambda x: x[2][2])
    chat_rooms = actives + inactives

    return render_template(
        "chat.html",
        requestCount=helper_connections.get_connection_request_count(),
        username=session["username"],
        rooms=chat_rooms,
        showChat=False,
        notifications=helper_general.get_notifications(),
    )


@chat_blueprint.route("/chat/<username>")
def chat_username(username):
    chat_rooms = helper_general.get_all_connections(session["username"])
    chat_rooms = list(
        map(lambda x: (x[0], helper_profile.get_profile_picture(x[0])), chat_rooms)
    )

    """with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT sender, receiver, message FROM "
            "PrivateMessages WHERE (sender=? OR receiver=?);", (session[
            "username"], username))"""
    
    messages = helper_general.get_messages(username)

    return render_template(
        "chat.html",
        requestCount=helper_connections.get_connection_request_count(),
        username=session["username"],
        rooms=chat_rooms,
        showChat=True,
        room=username,
        messages=messages,
        notifications=helper_general.get_notifications(),
    )
