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
db_path = os.path.join(BASE_DIR, "db.sqlite3")


@chat_blueprint.route("/chat")
def chat():

    chat_rooms = helper_general.get_rooms()

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

    chat_rooms = helper_general.get_rooms()

    messages = helper_general.get_messages(username)[0]

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
