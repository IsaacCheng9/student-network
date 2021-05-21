"""
Handles the view for user connections and related functionality.
"""

import sqlite3
from datetime import date

import student_network.helpers.helper_achievements as helper_achievements
import student_network.helpers.helper_connections as helper_connections
import student_network.helpers.helper_general as helper_general
import student_network.helpers.helper_profile as helper_profile
from flask import Blueprint, redirect, render_template, request, session

connections_blueprint = Blueprint(
    "connections", __name__, static_folder="static", template_folder="templates"
)


@connections_blueprint.route("/close_connection/<username>", methods=["GET", "POST"])
def close_connection(username: str) -> object:
    """
    Sends a connect request to another user on the network.

    Args:
        username: The username of the person to request a connection with.

    Returns:
        Redirection to the profile of the user they want to connect with.
    """
    if session["username"] != username:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Accounts WHERE username=?;", (username,))
            if cur.fetchone():
                conn_type = helper_connections.get_connection_type(username)
                if conn_type == "connected":
                    cur.execute(
                        "SELECT * FROM CloseFriend WHERE " "(user1=? AND user2=?);",
                        (session["username"], username),
                    )
                    if cur.fetchone() is None:
                        # Gets user from database using username.
                        cur.execute(
                            "INSERT INTO CloseFriend (user1, user2) " "VALUES (?,?);",
                            (
                                session["username"],
                                username,
                            ),
                        )
                        conn.commit()
                        session["add"] = True

                        helper_achievements.update_close_connection_achievements(cur)
        session["add"] = "You can't connect with yourself!"

    return redirect("/profile/" + username)


@connections_blueprint.route("/connect_request/<username>", methods=["GET", "POST"])
def connect_request(username: str) -> object:
    """
    Sends a connect request to another user on the network.

    Args:
        username: The username of the person to request a connection with.

    Returns:
        Redirection to the profile of the user they want to connect with.
    """
    if session["username"] != username:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Accounts WHERE username=?;", (username,))
            if cur.fetchone():
                cur.execute(
                    "SELECT * FROM Connection WHERE (user1=? AND user2=?) OR "
                    "(user1=? AND user2=?);",
                    (username, session["username"], session["username"], username),
                )
                if cur.fetchone() is None:
                    # Gets user from database using username.
                    cur.execute(
                        "INSERT INTO Connection (user1, user2, "
                        "connection_type) VALUES (?,?,?);",
                        (
                            session["username"],
                            username,
                            "request",
                        ),
                    )
                    conn.commit()
                    session["add"] = True

                    # Award achievement ID 17 - Getting social if necessary
                    cur.execute(
                        "SELECT * FROM CompleteAchievements "
                        "WHERE (username=? AND achievement_ID=?);",
                        (session["username"], 17),
                    )
                    if cur.fetchone() is None:
                        cur.execute(
                            "INSERT INTO CompleteAchievements "
                            "(username, achievement_ID, date_completed) "
                            "VALUES (?,?,?);",
                            (session["username"], 17, date.today()),
                        )
                        conn.commit()

        session["add"] = "You can't connect with yourself!"

    return redirect("/profile/" + username)


@connections_blueprint.route("/unblock_user/<username>", methods=["GET", "POST"])
def unblock_user(username: str) -> object:
    """
    Unblocks a given user.

    Args:
        username: The user to unblock.

    Returns:
        Redirection to the unblocked user's profile page.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Accounts WHERE username=?;", (username,))
        if cur.fetchone():
            if helper_connections.get_connection_type(username) == "block":
                if username != session["username"]:
                    cur.execute(
                        "DELETE FROM Connection WHERE (user1=? AND user2=?);",
                        (session["username"], username),
                    )
                    conn.commit()
    return redirect(session["prev-page"])


@connections_blueprint.route("/members", methods=["GET"])
def members() -> object:
    """
    Displays all members registered to the student network.

    Returns:
        The web page for displaying members.
    """
    session["prev-page"] = request.url
    return render_template(
        "members.html",
        requestCount=helper_connections.get_connection_request_count(),
        notifications=helper_general.get_notifications(),
    )


@connections_blueprint.route(
    "/accept_connection_request/<username>", methods=["GET", "POST"]
)
def accept_connection_request(username: str) -> object:
    """
    Accepts the connect request from another user on the network.

    Args:
        username: The username of the person who requested a connection.

    Returns:
        Redirection to the profile of the user they want to connect with.
    """
    if session["username"] != username:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Accounts WHERE username=?;", (username,))
            if cur.fetchone():
                row = cur.execute(
                    "SELECT * FROM Connection WHERE (user1=? AND user2=?) OR "
                    "(user1=? AND user2=?);",
                    (username, session["username"], session["username"], username),
                )
                if row:
                    # Gets user from database using username.
                    cur.execute(
                        "UPDATE Connection SET connection_type = ? "
                        "WHERE (user1=? AND user2=?) OR (user1=? AND "
                        "user2=?);",
                        (
                            "connected",
                            username,
                            session["username"],
                            session["username"],
                            username,
                        ),
                    )
                    conn.commit()
                    session["add"] = True

                    helper_achievements.update_connection_achievements(cur, username)
    else:
        session["add"] = "You can't connect with yourself!"

    return redirect(session["prev-page"])


@connections_blueprint.route("/block_user/<username>")
def block_user(username: str) -> object:
    """
    Blocks the given user.

    Args:
        username: The user to block.

    Returns:
        Redirection to the profile page of the user who has been blocked.
    """
    deleted = helper_connections.delete_connection(username)
    if deleted:
        if username != session["username"]:
            with sqlite3.connect("database.db") as conn:
                cur = conn.cursor()
                # Gets user from database using username.
                cur.execute(
                    "INSERT INTO Connection (user1, user2, "
                    "connection_type) VALUES (?,?,?);",
                    (
                        session["username"],
                        username,
                        "block",
                    ),
                )
                conn.commit()
    return redirect("/profile/" + username)


@connections_blueprint.route("/remove_close_friend/<username>")
def remove_close_friend(username: str) -> object:
    """
    Removes a connection with the given user.

    Args:
        username: The user they want to remove the connection with.

    Returns:
        Redirection to the previous page the user was on.
    """
    # Checks that the user isn't trying to remove a connection with
    # themselves.
    if username != session["username"]:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Accounts WHERE username=?;", (username,))
            # Searches for the connection in the database.
        if helper_connections.get_connection_type(username) == "connected":
            cur.execute(
                "SELECT * FROM CloseFriend WHERE (user1=? AND user2=?);",
                (session["username"], username),
            )
            if cur.fetchone():
                cur.execute(
                    "DELETE FROM CloseFriend WHERE (user1=? AND user2=?);",
                    (session["username"], username),
                )
                conn.commit()

    return redirect(session["prev-page"])


@connections_blueprint.route("/remove_connection/<username>")
def remove_connection(username: str) -> object:
    """
    Removes a connection with the given user.

    Args:
        username: The user they want to remove the connection with.

    Returns:
        Redirection to the previous page the user was on.
    """
    helper_connections.delete_connection(username)
    return redirect(session["prev-page"])


@connections_blueprint.route("/requests", methods=["GET", "POST"])
def show_connect_requests() -> object:
    """
    Shows connect requests made to the user.

    Returns:
        The web page for viewing connect requests.
    """
    with sqlite3.connect("database.db") as conn:
        # Loads the list of connection requests and their avatars.
        requests = []
        avatars = []
        cur = conn.cursor()

        # Extracts incoming requests.
        cur.execute(
            "SELECT Connection.user1, UserProfile.profilepicture FROM "
            "Connection LEFT JOIN UserProfile ON Connection.user1 = "
            "UserProfile.username WHERE user2=? AND connection_type=?;",
            (session["username"], "request"),
        )
        conn.commit()
        row = cur.fetchall()
        if len(row) > 0:
            for elem in row:
                requests.append(elem[0])
                avatars.append(elem[1])

        # Extracts connections.
        cur.execute(
            "SELECT Connection.user1, UserProfile.profilepicture FROM "
            "Connection LEFT JOIN UserProfile ON Connection.user1 = "
            "UserProfile.username WHERE user2=? AND connection_type=?;",
            (session["username"], "connected"),
        )
        connections1 = cur.fetchall()
        cur.execute(
            "SELECT Connection.user2, UserProfile.profilepicture FROM "
            "Connection LEFT JOIN UserProfile ON Connection.user2 = "
            "UserProfile.username WHERE user1=? AND connection_type=?;",
            (session["username"], "connected"),
        )
        connections2 = cur.fetchall()

        # Extracts pending requests.
        cur.execute(
            "SELECT Connection.user2, UserProfile.profilepicture FROM "
            "Connection LEFT JOIN UserProfile ON Connection.user2 = "
            "UserProfile.username WHERE user1=? AND connection_type=?;",
            (session["username"], "request"),
        )
        pending_connections = cur.fetchall()

        # Extracts blocked users.
        cur.execute(
            "SELECT Connection.user2, UserProfile.profilepicture FROM "
            "Connection LEFT JOIN UserProfile ON Connection.user2 = "
            "UserProfile.username WHERE user1=? AND connection_type=?;",
            (session["username"], "block"),
        )
        blocked_connections = cur.fetchall()

        # Extracts mutual connections.
        recommended_connections = helper_connections.get_recommended_connections(
            session["username"]
        )
        mutual_avatars = []
        for mutual in recommended_connections:
            mutual_avatars.append(helper_profile.get_profile_picture(mutual[0]))

        # Lists usernames of all connected people.
        connections = connections1 + connections2
        # Adds a close friend to the list, and sorts by close friends first.
        connections = list(
            map(
                lambda x: (
                    x[0],
                    x[1],
                    helper_connections.is_close_friend(session["username"], x[0]),
                ),
                connections,
            )
        )
        connections = sorted(connections, key=lambda x: x[2], reverse=True)

    session["prev-page"] = request.url
    return render_template(
        "request.html",
        requests=requests,
        avatars=avatars,
        allUsernames=helper_general.get_all_usernames(),
        requestCount=helper_connections.get_connection_request_count(),
        connections=connections,
        pending=pending_connections,
        blocked=blocked_connections,
        mutuals=recommended_connections,
        mutual_avatars=mutual_avatars,
        notifications=helper_general.get_notifications(),
    )
