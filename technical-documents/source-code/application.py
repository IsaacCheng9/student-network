"""
A student network application which is presented as a web application using
the Flask module. Students each have their own profile page, and they can post
on their feed.
"""
import os
import re
import sqlite3
import uuid
from datetime import date, datetime
from string import capwords
from typing import Tuple, List

from PIL import Image
from email_validator import validate_email, EmailNotValidError
from flask import Flask, render_template, request, redirect, session
from passlib.hash import sha256_crypt
from werkzeug.utils import secure_filename

application = Flask(__name__)
application.secret_key = ("\xfd{H\xe5 <\x95\xf9\xe3\x96.5\xd1\x01O <!\xd5\""
                          "xa2\xa0\x9fR\xa1\xa8")
application.url_map.strict_slashes = False
application.config['UPLOAD_FOLDER'] = '/static/images'


@application.route("/", methods=["GET"])
def index_page():
    """
    Renders the feed page if the user is logged in.

    Returns:
        The web page for user login.
    """
    if "username" in session:
        return redirect("/profile")
    else:
        return redirect("/login")


@application.route("/login", methods=["GET"])
def login_page():
    """
    Renders the login page.

    Returns:
        The web page for user login.
    """
    errors = []
    if "username" in session:
        return redirect("/profile")
    else:
        if "error" in session:
            errors = session["error"]
        session["prev-page"] = request.url
        # Clear error session variables.
        session.pop("error", None)
        return render_template("login.html", errors=errors)


@application.route("/close_connection/<username>", methods=["GET", "POST"])
def close_connection(username):
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
            cur.execute("SELECT * FROM Accounts WHERE username=?;",
                        (username,))
            if cur.fetchone() is not None:
                conn_type = get_connection_type(username)
                if conn_type == "connected":
                    cur.execute(
                        "SELECT * FROM CloseFriend WHERE "
                        "(user1=? AND user2=?);",
                        (session["username"], username))
                    if cur.fetchone() is None:
                        # Gets user from database using username.
                        cur.execute(
                            "INSERT INTO CloseFriend (user1, user2) "
                            "VALUES (?,?);",
                            (session["username"], username,))
                        conn.commit()
                        session["add"] = True

                        # Award achievement ID 12 - Friends if necessary
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (session["username"], 12))
                        if cur.fetchone() is None:
                            apply_achievement(session["username"], 12)

                        # Award achievement ID 13 - Friend Group if necessary
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (session["username"], 13))
                        if cur.fetchone() is None:
                            cur.execute(
                                "SELECT * FROM CloseFriend WHERE user1=?;",
                                (session["username"],))
                            if len(cur.fetchall()) >= 10:
                                apply_achievement(session["username"], 13)
        session["add"] = "You can't connect with yourself!"

    return redirect("/profile/" + username)


@application.route("/connect_request/<username>", methods=["GET", "POST"])
def connect_request(username):
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
            cur.execute("SELECT * FROM Accounts WHERE username=?;",
                        (username,))
            if cur.fetchone() is not None:
                cur.execute(
                    "SELECT * FROM Connection WHERE (user1=? AND user2=?) OR "
                    "(user1=? AND user2=?);",
                    (username, session["username"], session["username"],
                     username))
                if cur.fetchone() is None:
                    # Gets user from database using username.
                    cur.execute(
                        "INSERT INTO Connection (user1, user2, "
                        "connection_type) VALUES (?,?,?);",
                        (session["username"], username, "request",))
                    conn.commit()
                    session["add"] = True

                    # Award achievement ID 17 - Getting social if necessary
                    cur.execute(
                        "SELECT * FROM CompleteAchievements "
                        "WHERE (username=? AND achievement_ID=?);",
                        (session["username"], 17))
                    if cur.fetchone() is None:
                        cur.execute(
                            "INSERT INTO CompleteAchievements "
                            "(username, achievement_ID, date_completed) "
                            "VALUES (?,?,?);",
                            (session["username"], 17, date.today()))
                        conn.commit()

        session["add"] = "You can't connect with yourself!"

    return redirect("/profile/" + username)


@application.route("/unblock_user/<username>", methods=["GET","POST"])
def unblock_user(username):
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Accounts WHERE username=?;",
                    (username,))
        if cur.fetchone() is not None:
            if get_connection_type(username) == "block":
                if username != session['username']:
                    cur.execute(
                        "DELETE FROM Connection WHERE (user1=? AND user2=?);",
                        (session["username"], username))
                    conn.commit()
    return redirect("/profile/" + username)


@application.route("/members", methods=["GET"])
def members() -> object:
    return render_template("members.html",
                           requestCount=get_connection_request_count())


@application.route("/leaderboard", methods=["GET"])
def leaderboard() -> object:
    """
    Display leaderboard of users with the most experience
    Returns:
        The web page for viewing Rankings.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM UserLevel; ")
        if cur.fetchone() is not None:
            topUsers = cur.fetchall()
            totalUserCount = len(topUsers)
            # 0 = username
            # 1 = XP value
            topUsers.sort(key=lambda x: x[1], reverse=True)

            myRanking = 0
            for user in topUsers:
                myRanking += 1
                if user[0] == session["username"]:
                    break

            topUsers = topUsers[0:min(25, len(topUsers))]

            topUsers = list(map(lambda x: (
            x[0], x[1], get_profile_picture(x[0]), get_level(x[0])), topUsers))

    return render_template("/leaderboard.html", leaderboard=topUsers,
                           requestCount=get_connection_request_count(),
                           allUsernames=get_all_usernames(),
                           myRanking=myRanking, totalUserCount=totalUserCount)


@application.route("/achievements", methods=["GET"])
def achievements() -> object:
    """
    Display achievements which the user has unlocked/locked.

    Returns:
        The web page for viewing achievements.
    """

    unlocked_achievements, locked_achievements = get_achievements(
        session["username"])

    percentage = int(100 * len(unlocked_achievements) /
                     (len(unlocked_achievements) + len(locked_achievements)))
    percentage_color = "green"
    if percentage < 66:
        percentage_color = "orange"
    if percentage < 33:
        percentage_color = "red"

    # Award achievement ID 3 - Show it off if necessary
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM CompleteAchievements "
            "WHERE (username=? AND achievement_ID=?);",
            (session["username"], 3))
        if cur.fetchone() is None:
            apply_achievement(session["username"], 3)

    return render_template("achievements.html",
                           unlocked_achievements=unlocked_achievements,
                           locked_achievements=locked_achievements,
                           requestCount=get_connection_request_count(),
                           allUsernames=get_all_usernames(),
                           percentage=percentage,
                           percentage_color=percentage_color)


@application.route("/accept_connection_request/<username>",
                   methods=["GET", "POST"])
def accept_connection_request(username) -> object:
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
            cur.execute("SELECT * FROM Accounts WHERE username=?;",
                        (username,))
            if cur.fetchone() is not None:
                row = cur.execute(
                    "SELECT * FROM Connection WHERE (user1=? AND user2=?) OR "
                    "(user1=? AND user2=?);",
                    (username, session["username"], session["username"],
                     username))
                if row is not None:
                    # Gets user from database using username.
                    cur.execute(
                        "UPDATE Connection SET connection_type = ? "
                        "WHERE (user1=? AND user2=?) OR (user1=? AND "
                        "user2=?);",
                        ("connected", username, session["username"],
                         session["username"],
                         username))
                    conn.commit()
                    session["add"] = True

                    # Award achievement ID 4 - Connected if necessary
                    cur.execute(
                        "SELECT * FROM CompleteAchievements "
                        "WHERE (username=? AND achievement_ID=?);",
                        (session["username"], 4))
                    if cur.fetchone() is None:
                        apply_achievement(session["username"], 4)

                    # Award achievement ID 4 to connected user
                    cur.execute(
                        "SELECT * FROM CompleteAchievements "
                        "WHERE (username=? AND achievement_ID=?);",
                        (username, 4))
                    if cur.fetchone() is None:
                        apply_achievement(username, 4)

                    # Get user interests and hobbies
                    cur.execute(
                        "SELECT interest FROM UserInterests "
                        "WHERE username=?;",
                        (session["username"],))
                    row = cur.fetchall()
                    my_interests = []
                    for interest in row:
                        my_interests.append(interest[0])
                    cur.execute(
                        "SELECT hobby FROM UserHobby "
                        "WHERE username=?;",
                        (session["username"],))
                    row = cur.fetchall()
                    my_hobbies = []
                    for hobby in row:
                        my_hobbies.append(hobby[0])

                    # Get connected user interests and hobbies
                    cur.execute(
                        "SELECT interest FROM UserInterests "
                        "WHERE username=?;",
                        (username,))
                    row = cur.fetchall()
                    conec_interests = []
                    for interest in row:
                        conec_interests.append(interest[0])
                    cur.execute(
                        "SELECT hobby FROM UserHobby "
                        "WHERE username=?;",
                        (username,))
                    row = cur.fetchall()
                    conec_hobbies = []
                    for hobby in row:
                        conec_hobbies.append(hobby[0])
                    
                    # Award achievement ID 16 - Shared intrests if necessary
                    common_interests = set(my_interests) - (set(my_interests) - set(conec_interests))
                    print(common_interests)
                    if common_interests:
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (session["username"], 16))
                        if cur.fetchone() is None:
                            apply_achievement(session["username"], 16)

                        # Award achievement ID 16 to connected user        
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (username, 16))
                        if cur.fetchone() is None:
                            apply_achievement(username, 16)

                    # Award achievement ID 26 - Shared hobbies if necessary
                    common_hobbies = set(my_hobbies) - (set(my_hobbies) - set(conec_hobbies))
                    print(common_hobbies)
                    if common_hobbies:
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (session["username"], 26))
                        if cur.fetchone() is None:
                            apply_achievement(session["username"], 26)

                        # Award achievement ID 26 to connected user   
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (username, 26))
                        if cur.fetchone() is None:
                            apply_achievement(username, 26)
                    
                        

                    # Get connections
                    cons_user = get_all_connections(session["username"])

                    # Get connections
                    cons_user2 = get_all_connections(username)

                    # Get user degree and connections different
                    cur.execute(
                        "SELECT degree from UserProfile "
                        "WHERE username=?;", (session["username"],)
                    )
                    degree = cur.fetchone()[0]
                    cur.execute(
                        "SELECT degree from UserProfile "
                        "WHERE username=?;", (username,)
                    )
                    degree_user2 = cur.fetchone()[0]
                    
                    # Get count of connections who study a different degree
                    valid_user_count = 0
                    for user in cons_user:
                        cur.execute(
                            "SELECT username from UserProfile "
                            "WHERE degree!=? AND username=?;",
                            (degree, user[0])
                        )
                        if cur.fetchone():
                            valid_user_count += 1

                    # Get count of other user connections who study a different degree
                    valid_user_count2 = 0
                    for user in cons_user2:
                        cur.execute(
                            "SELECT username from UserProfile "
                            "WHERE degree!=? AND username=?;",
                            (degree_user2, user[0])
                        )
                        if cur.fetchone():
                            valid_user_count2 += 1

                    # Award achievement ID 14 - Reaching out if necessary
                    if valid_user_count >= 1:
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (session["username"], 14))
                        if cur.fetchone() is None:
                            apply_achievement(session["username"], 14)

                    # Award achievement ID 14 to connected user
                    if valid_user_count2 >= 1:
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (username, 14))
                        if cur.fetchone() is None:
                            apply_achievement(username, 14)

                    # Award achievement ID 15 - Outside your bubble if necessary
                    if valid_user_count >= 10:
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (session["username"], 15))
                        if cur.fetchone() is None:
                            apply_achievement(session["username"], 15)

                    # Award achievement ID 15 to connected user
                    if valid_user_count2 >= 10:
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (username, 15))
                        if cur.fetchone() is None:
                            apply_achievement(username, 15)

                    # Get number of connections
                    con_count_user = len(cons_user)

                    # Get number of connections
                    con_count_user2 = len(cons_user2)

                    # Award achievement ID 5 - Popular if necessary
                    if con_count_user >= 10:
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (session["username"], 5))
                        if cur.fetchone() is None:
                            apply_achievement(session["username"], 5)

                    # Award achievement ID 5 to connected user
                    if con_count_user2 >= 10:
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (username, 5))
                        if cur.fetchone() is None:
                            apply_achievement(username, 5)

                    # Award achievement ID 6 - Centre of Attention if necessary
                    if con_count_user >= 100:
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (session["username"], 6))
                        if cur.fetchone() is None:
                            apply_achievement(session["username"], 6)

                    # Award achievement ID 6 to connected user
                    if con_count_user2 >= 100:
                        cur.execute(
                            "SELECT * FROM CompleteAchievements "
                            "WHERE (username=? AND achievement_ID=?);",
                            (username, 6))
                        if cur.fetchone() is None:
                            apply_achievement(username, 6)
    else:
        session["add"] = "You can't connect with yourself!"

    return redirect(session["prev-page"])


@application.route("/block_user/<username>")
def block_user(username: str) -> object:
    deleted = delete_friend(username)
    if deleted: # if deleting was successful
        if username != session['username']:
            with sqlite3.connect("database.db") as conn:
                cur = conn.cursor()
                # Gets user from database using username.
                cur.execute(
                    "INSERT INTO Connection (user1, user2, "
                    "connection_type) VALUES (?,?,?);",
                    (session["username"], username, "block",))
                conn.commit()
    return redirect("/profile/" + username)



@application.route("/remove_close_friend/<username>")
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
    if username != session['username']:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Accounts WHERE username=?;",
                        (username,))
            # Searches for the connection in the database.
        if get_connection_type(username) == "connected":
            cur.execute(
                "SELECT * FROM CloseFriend WHERE (user1=? AND user2=?);",
                (session["username"], username))
            if cur.fetchone() is not None:
                cur.execute(
                    "DELETE FROM CloseFriend WHERE (user1=? AND user2=?);",
                    (session["username"], username))
                conn.commit()

    return redirect(session["prev-page"])


@application.route("/remove_connection/<username>")
def remove_connection(username: str) -> object:
    """
    Removes a connection with the given user.

    Args:
        username: The user they want to remove the connection with.
    Returns:
        Redirection to the previous page the user was on.
    """
    delete_friend(username)
    return redirect(session["prev-page"])


def delete_friend(username):
    # Checks that the user isn't trying to remove a connection with
    # themselves.
    if username != session['username']:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Accounts WHERE username=?;",
                        (username,))

            # Searches for the connection in the database.
            if cur.fetchone() is not None:
                row = cur.execute(
                    "SELECT * FROM Connection WHERE (user1=? AND user2=?) OR "
                    "(user1=? AND user2=?);",
                    (username, session["username"], session["username"],
                     username))
                # Removes the connection from the database if it exists.
                if row is not None:
                    cur.execute(
                        "DELETE FROM Connection WHERE (user1=? AND user2=?) "
                        "OR (user1=? AND user2=?);",
                        (username, session["username"], session["username"],
                         username))
                    row = cur.execute(
                        "SELECT * FROM Connection "
                        "WHERE (user1=? AND user2=?) "
                        "OR (user1=? AND user2=?);",
                        (username, session["username"], session["username"],
                         username))
                    if row is not None:
                        cur.execute(
                            "DELETE FROM CloseFriend "
                            "WHERE (user1=? AND user2=?) "
                            "OR (user1=? AND user2=?);",
                            (username, session["username"],
                             session["username"], username))
                    conn.commit()    
                    return True
                else:
                    return True
            else:
                return False

@application.route("/requests", methods=["GET", "POST"])
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
            (session["username"], "request"))
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
            (session["username"], "connected"))
        connections1 = cur.fetchall()
        cur.execute(
            "SELECT Connection.user2, UserProfile.profilepicture FROM "
            "Connection LEFT JOIN UserProfile ON Connection.user2 = "
            "UserProfile.username WHERE user1=? AND connection_type=?;",
            (session["username"], "connected"))
        connections2 = cur.fetchall()

        # Extracts pending requests.
        cur.execute(
            "SELECT Connection.user2, UserProfile.profilepicture FROM "
            "Connection LEFT JOIN UserProfile ON Connection.user2 = "
            "UserProfile.username WHERE user1=? AND connection_type=?;",
            (session["username"], "request"))
        pending_connections = cur.fetchall()

        # Lists usernames of all connected people.
        connections = connections1 + connections2
        # Adds a close friend to the list, and sorts by close friends first.
        connections = list(
            map(lambda x: (x[0], x[1], is_close_friend(x[0])), connections))
        connections = sorted(connections, key=lambda x: x[2], reverse=True)

    session["prev-page"] = request.url

    return render_template("request.html", requests=requests, avatars=avatars,
                           allUsernames=get_all_usernames(),
                           requestCount=get_connection_request_count(),
                           connections=connections,
                           pending=pending_connections)


@application.route("/terms", methods=["GET", "POST"])
def terms_page():
    """
    Renders the terms and conditions page.

    Returns:
        The web page for T&Cs, or redirection back to register page.
    """
    if request.method == "GET":
        session["prev-page"] = request.url
        return render_template("terms.html",
                               requestCount=get_connection_request_count())
    else:
        return redirect("/register")


@application.route("/privacy_policy", methods=["GET", "POST"])
def privacy_policy_page():
    """
    Renders the privacy policy page.

    Returns:
        The web page for the privacy policy, or redirection back to T&C.
    """
    if request.method == "GET":
        session["prev-page"] = request.url
        return render_template("privacy_policy.html",
                               requestCount=get_connection_request_count())
    else:
        return redirect("/terms")


@application.route("/login", methods=["POST"])
def login_submit():
    """
    Validates the user's login details.

    Returns:
         Redirection depending on whether login was successful or not.
    """
    username = request.form["username_input"].lower()
    psw = request.form["psw_input"]

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # Gets user from database using username.
        cur.execute(
            "SELECT password FROM Accounts WHERE username=?;", (username,))
        conn.commit()
        row = cur.fetchone()
        if row is not None:
            hashed_psw = row[0]
        else:
            session["error"] = ["login"]
            return redirect("/login")
        if hashed_psw is not None:
            if sha256_crypt.verify(psw, hashed_psw):
                session["username"] = username
                session["prev-page"] = request.url
                return redirect("/profile")
            else:
                session["error"] = ["login"]
                return redirect("/login")
        else:
            session["error"] = ["login"]
            return redirect("/login")


@application.route("/error", methods=["GET"])
def error_test():
    """
    Redirects the user back to the login page if an error occurred.

    Returns:
        Redirection to the login page.
    """
    session["error"] = ["login"]
    return redirect("/login")


@application.route("/register", methods=["GET"])
def register_page():
    """
    Renders the user registration page.

    Returns:
        The web page for user registration.
    """
    notifications = []
    errors = ""
    if "username" in session:
        return redirect("/profile")
    else:
        if "notifications" in session:
            notifications = session["notifications"]
        if "error" in session:
            errors = session["error"]
        session.pop("error", None)
        session.pop("notifications", None)
        session["prev-page"] = request.url

        return render_template("register.html", notifications=notifications,
                               errors=errors,
                               requestCount=get_connection_request_count())


@application.route("/register", methods=["POST"])
def register_submit() -> object:
    """
    Registers an account using the user's input from the registration form.

    Returns:
        The updated web page based on whether the details provided were valid.
    """
    # Obtains user input from the account registration form.
    username = request.form["username_input"].lower()
    full_name = capwords(request.form["fullname_input"])
    password = request.form["psw_input"]
    password_confirm = request.form["psw_input_check"]
    email = request.form["email_input"]
    terms = request.form.get("terms")

    # Connects to the database to perform validation.
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        valid, message = validate_registration(cur, username, full_name,
                                               password, password_confirm,
                                               email, terms)
        # Registers the user if the details are valid.
        if valid is True:
            hash_password = sha256_crypt.hash(password)
            cur.execute(
                "INSERT INTO Accounts (username, password, email, type) "
                "VALUES (?, ?, ?, ?);", (username, hash_password, email,
                                         "student",))
            cur.execute(
                "INSERT INTO UserProfile (username, name, bio, gender, "
                "birthday, profilepicture) "
                "VALUES (?, ?, ?, ?, ?, ?);", (
                    username, full_name, "Change your bio in the settings.",
                    "Male", date.today(), "/static/images/default-pfp.jpg",))

            check_level_exists(username, conn)

            conn.commit()

            session["notifications"] = ["register"]
            session["username"] = username

            return redirect("/register")
        # Displays error message(s) stating why their details are invalid.
        else:
            session["error"] = message
            return redirect("/register")


@application.route("/post_page/<post_id>", methods=["GET"])
def post(post_id):
    """
    Loads a post and comments on that post.

    Returns:
        Redirection to the post page.
    """
    comments = {"comments": []}
    message = []
    author = ""
    session["prev-page"] = request.url
    content = None
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # Gets user from database using username.
        cur.execute(
            "SELECT title, body, username, date, account_type, likes, post_type "
            "FROM POSTS WHERE postId=?;", (post_id,))
        row = cur.fetchall()
        if len(row) == 0:
            message.append("This post does not exist.")
            message.append(
                "Please ensure you have entered the name correctly.")
            session["prev-page"] = request.url
            return render_template("error.html", message=message,
                                   requestCount=get_connection_request_count(),
                                   allUsernames=get_all_usernames())
        else:
            data = row[0]
            title, body, username, date_posted, account_type, likes, post_type = (
                data[0], data[1],
                data[2], data[3],
                data[4], data[5], data[6])
            if post_type == "Image":
                cur.execute(
                    "SELECT contentUrl "
                    "FROM PostContent WHERE postId=?;", (post_id,))
                content = cur.fetchone()[0]
                print(content)
            cur.execute(
                "SELECT *"
                "FROM Comments WHERE postId=?;", (post_id,))
            row = cur.fetchall()
            if len(row) == 0:
                return render_template(
                    "post_page.html", author=author, postId=post_id,
                    title=title, body=body, username=username,
                    date=date_posted, likes=likes, accountType=account_type,
                    comments=None, requestCount=get_connection_request_count(),
                    allUsernames=get_all_usernames(),
                    avatar=get_profile_picture(username), type=post_type,
                    content=content)
            for comment in row:
                time = datetime.strptime(
                    comment[3], "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%y %H:%M")
                comments["comments"].append({
                    "commentId": comment[0],
                    "username": comment[1],
                    "body": comment[2],
                    "date": time,
                })

            return render_template(
                "post_page.html", author=author, postId=post_id, title=title,
                body=body, username=username, date=date_posted, likes=likes,
                accountType=account_type, comments=comments,
                requestCount=get_connection_request_count(),
                allUsernames=get_all_usernames(),
                avatar=get_profile_picture(username))


@application.route("/feed", methods=["GET"])
def feed():
    """
    Checks user is logged in before viewing their feed page.

    Returns:
        Redirection to their feed if they're logged in.
    """
    content = ""
    if "username" in session:
        session["prev-page"] = request.url
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()

            connections = get_all_connections(session["username"])
            connections.append((session["username"],))
            row = []
            for user in connections:
                cur.execute(
                    "SELECT * FROM POSTS "
                    "WHERE username=? "
                    "AND privacy!='private' AND privacy!='close';", (user[0],))
                row += cur.fetchall()
            # Sort reverse chronologically
            row = sorted(row, key=lambda x: x[0], reverse=True)
            i = 0
            all_posts = {
                "AllPosts": []
            }
            # account type differentiation in posts db
            for user_post in row:
                if i == 50:
                    break
                add = ""
                if len(user_post[2]) > 250:
                    add = "..."
                time = datetime.strptime(user_post[4], '%Y-%m-%d').strftime(
                    '%d-%m-%y')

                # Get account type
                cur.execute("SELECT type "
                            "FROM ACCOUNTS WHERE username=? ",
                            (user_post[3],))

                print(get_profile_picture(user_post[3]))
                accounts = cur.fetchone()
                account_type = accounts[0]

                post_id = user_post[0]
                post_type = user_post[8]
                if post_type == "Image":
                    cur.execute(
                        "SELECT contentUrl "
                        "FROM PostContent WHERE postId=?;", (post_id,))
                    content = cur.fetchone()

                all_posts["AllPosts"].append({
                    "postId": user_post[0],
                    "title": user_post[1],
                    "profile_pic": get_profile_picture(user_post[3]),
                    "author": user_post[3],
                    "account_type": account_type,
                    "date_posted": time,
                    "body": (user_post[2])[:250] + add,
                    "post_type": user_post[8],
                    "content": content
                })
                i += 1

        # Displays any error messages.
        if "error" in session:
            errors = session["error"]
            session.pop("error", None)

            return render_template("feed.html", posts=all_posts,
                                   requestCount=get_connection_request_count(),
                                   allUsernames=get_all_usernames(),
                                   errors=errors, content=content)
        else:
            return render_template("feed.html", posts=all_posts,
                                   requestCount=get_connection_request_count(),
                                   allUsernames=get_all_usernames(),content=content )
    else:
        return redirect("/login")


@application.route("/submit_post", methods=["POST"])
def submit_post():
    """
    Submit post on social wall to database.

    Returns:
        Updated feed with new post added
    """
    form_type = request.form.get("form_type")
    postPrivacy = request.form.get("privacy")

    if form_type == "Quiz":
        # Gets quiz details.
        quiz_name = request.form.get("quiz_name")
        question_1 = [request.form.get("question_1"),
                      request.form.get("question_1_ans_1"),
                      request.form.get("question_1_ans_2"),
                      request.form.get("question_1_ans_3"),
                      request.form.get("question_1_ans_4")]
        question_2 = [request.form.get("question_2"),
                      request.form.get("question_2_ans_1"),
                      request.form.get("question_2_ans_2"),
                      request.form.get("question_2_ans_3"),
                      request.form.get("question_2_ans_4")]
        question_3 = [request.form.get("question_3"),
                      request.form.get("question_3_ans_1"),
                      request.form.get("question_3_ans_2"),
                      request.form.get("question_3_ans_3"),
                      request.form.get("question_3_ans_4")]
        question_4 = [request.form.get("question_4"),
                      request.form.get("question_4_ans_1"),
                      request.form.get("question_4_ans_2"),
                      request.form.get("question_4_ans_3"),
                      request.form.get("question_4_ans_4")]
        question_5 = [request.form.get("question_5"),
                      request.form.get("question_5_ans_1"),
                      request.form.get("question_5_ans_2"),
                      request.form.get("question_5_ans_3"),
                      request.form.get("question_5_ans_4")]
        print(quiz_name)

        # Adds quiz to the database.
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO Quiz (quiz_name, question_1, "
                        "question_1_ans_1, question_1_ans_2, question_1_ans_3, "
                        "question_1_ans_4, question_2, question_2_ans_1, "
                        "question_2_ans_2, question_2_ans_3, question_2_ans_4, "
                        "question_3, question_3_ans_1, question_3_ans_2, "
                        "question_3_ans_3, question_3_ans_4, question_4, "
                        "question_4_ans_1, question_4_ans_2, question_4_ans_3, "
                        "question_4_ans_4, question_5, question_5_ans_1, "
                        "question_5_ans_2, question_5_ans_3, question_5_ans_4, "
                        "privacy) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                        "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                        (
                            quiz_name, question_1[0], question_1[1],
                            question_1[2],
                            question_1[3], question_1[4], question_2[0],
                            question_2[1], question_2[2], question_2[3],
                            question_2[4], question_3[0], question_3[1],
                            question_3[2], question_3[3], question_3[4],
                            question_4[0], question_4[1], question_4[2],
                            question_4[3], question_4[4], question_5[0],
                            question_5[1], question_5[2], question_5[3],
                            question_5[4], postPrivacy))
            conn.commit()
    else:
        post_title = request.form["post_title"]
        post_body = request.form["post_text"]

        if form_type == "Image":
            file = request.files["file"]
            file_name_hashed = ""
            # Hashes the name of the file and resizes it.
            if allowed_file(file.filename):
                secure_filename(file.filename)
                file_name_hashed = str(uuid.uuid4())
                file_path = os.path.join(
                    "." + application.config["UPLOAD_FOLDER"] + "//post_imgs",
                    file_name_hashed)
                im = Image.open(file)
                im = im.resize((400, 400))
                im = im.convert("RGB")
                im.save(file_path + ".jpg")
            elif file:
                valid = False
                # message.append("Your file must be an image.")

        elif form_type == "Link":
            link = request.form.get("link")

        # Only adds the post if a title has been input.
        if post_title != "":
            with sqlite3.connect("database.db") as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO POSTS (title, body, username, post_type, privacy) "
                            "VALUES (?, ?, ?, ?, ?);",
                            (
                                post_title, post_body, session["username"],
                                form_type, postPrivacy))
                conn.commit()

                if form_type == "Image" and valid == True:
                    cur.execute("INSERT INTO PostContent (postId, contentUrl) "
                                "VALUES (?, ?);",
                                (cur.lastrowid, application.config[
                                    "UPLOAD_FOLDER"] + "//post_imgs/" + file_name_hashed + ".jpg"))
                    conn.commit()

                # Award achievement ID 7 - Express yourself if necessary
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (session["username"], 7))
                if cur.fetchone() is None:
                    apply_achievement(session["username"], 7)

                # Award achievement ID 8 - 5 posts if necessary
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (session["username"], 8))
                if cur.fetchone() is None:
                    cur.execute(
                        "SELECT * FROM POSTS WHERE username=?;",
                        (session["username"],))
                    results = cur.fetchall()
                    if len(results) >= 5:
                        apply_achievement(session["username"], 8)

                # Award achievement ID 9 - 20 posts if necessary
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (session["username"], 9))
                if cur.fetchone() is None:
                    cur.execute(
                        "SELECT * FROM POSTS WHERE username=?;",
                        (session["username"],))
                    results = cur.fetchall()
                    if len(results) >= 20:
                        apply_achievement(session["username"], 9)
        else:
            # Prints error message stating that the title is missing.
            session["error"] = ["You must submit a post title!"]

    return redirect("/feed")


@application.route("/like_post", methods=["POST"])
def like_post():
    """
    Records liking a post to the database.

    Returns:
        Redirection to the post with like added.
    """
    post_id = request.form["postId"]

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # check user hasn't liked post already
        cur.execute("SELECT username, postId FROM UserLikes"
                    " WHERE postId=? AND username=? ;",
                    (post_id, session["username"]))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO UserLikes (postId,username)"
                        "VALUES (?, ?);", (post_id, session["username"]))

            # Gets number of current likes.
            cur.execute("SELECT likes, username FROM POSTS WHERE postId=?;", (post_id,))
            row = cur.fetchone()
            likes = row[0] + 1
            username = row[1]

            cur.execute("UPDATE POSTS SET likes=? "
                        " WHERE postId=? ;", (likes, post_id,))
            conn.commit()

            # Award achievement ID 20 - First like if necessary
            cur.execute(
                "SELECT * FROM CompleteAchievements "
                "WHERE (username=? AND achievement_ID=?);",
                (username, 20))
            if cur.fetchone() is None:
                apply_achievement(username, 20)

            # Award achievement ID 22 - Everyone loves you if necessary
            if likes >= 50:
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (username, 22))
                if cur.fetchone() is None:
                    apply_achievement(username, 22)

            # Checks how many posts user has liked.
            cur.execute("SELECT COUNT(postId) FROM UserLikes"
                        " WHERE username=? ;", (session["username"],))
            row = cur.fetchone()[0]

            # Award achievement ID 19 - Liking that if necessary
            if row == 1:
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (session["username"], 19))
                if cur.fetchone() is None:
                    apply_achievement(session["username"], 19)

            # Award achievement ID 24 - Show the love if necessary
            elif row == 50:
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (session["username"], 24))
                if cur.fetchone() is None:
                    apply_achievement(session["username"], 24)

            # Award achievement ID 25 - Loving everything if necessary        
            elif row == 500:
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (session["username"], 25))
                if cur.fetchone() is None:
                    apply_achievement(session["username"], 25)

    return redirect("/post_page/" + post_id)


@application.route("/submit_comment", methods=["POST"])
def submit_comment():
    """
    Submit comment on post page to database.

    Returns:
        Updated post with new comment added
    """
    post_id = request.form["postId"]
    comment_body = request.form["comment_text"]

    # Only submits the comment if it is not empty.
    if comment_body.replace(" ", "") != "":
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO Comments (postId, body, username) "
                        "VALUES (?, ?, ?);",
                        (post_id, comment_body, session["username"]))
            conn.commit()

            # Award achievement ID 10 - Commentary if necessary
            cur.execute(
                "SELECT * FROM CompleteAchievements "
                "WHERE (username=? AND achievement_ID=?);",
                (session["username"], 10))
            if cur.fetchone() is None:
                apply_achievement(session["username"], 10)

    session["postId"] = post_id
    return redirect("/post_page/" + post_id)


@application.route("/delete_post", methods=["POST"])
def delete_post():
    """
    Deletes a post from the database.

    Returns:
        Renders a page stating that the post has been deleted successfully.
    """
    post_id = request.form["postId"]
    message = []

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT postId FROM POSTS WHERE postId=?;", (post_id,))
        row = cur.fetchone()
        # check the post exists in database
        if row[0] is None:
            message.append("Error: this post does not exist")
        else:
            cur.execute("DELETE FROM POSTS WHERE postId=?", (post_id,))
            conn.commit()

    message.append("Post has been deleted successfully.")
    return render_template("error.html", message=message,
                           requestCount=get_connection_request_count(),
                           allUsernames=get_all_usernames())


@application.route("/delete_comment", methods=["POST"])
def delete_comment():
    """
    Deletes a comment from the database.

    Returns:
        Redirection to the post page.
    """
    message = []
    post_id = request.form["postId"]
    comment_id = request.form["commentId"]

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Comments WHERE commentId=? ",
                    (comment_id,))
        row = cur.fetchone()
        # Checks that the comment exists.
        if row[0] is None:
            message.append("Comment does not exist.")
            return render_template("error.html", message=message,
                                   requestCount=get_connection_request_count(),
                                   allUsernames=get_all_usernames())
        else:
            cur.execute("DELETE FROM Comments WHERE commentId =? ",
                        (comment_id,))
            conn.commit()

    return redirect("post_page/" + post_id)


@application.route("/profile", methods=["GET"])
def user_profile():
    """
    Checks the user is logged in before viewing their profile page.

    Returns:
        Redirection to their profile if they're logged in.
    """
    if "username" in session:
        return redirect("/profile/" + session["username"])

    return redirect("/")


@application.route("/profile/<username>", methods=["GET"])
def profile(username):
    """
    Displays the user's profile page and fills in all of the necessary
    details. Hides the request buttons if the user is seeing their own page.

    Returns:
        The updated web page based on whether the details provided were valid.
    """
    email = ""
    hobbies = []
    interests = []
    message = []

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # Gets user from database using username.
        cur.execute(
            "SELECT name, bio, gender, birthday, profilepicture FROM "
            "UserProfile WHERE username=?;", (username,))
        row = cur.fetchall()
        if len(row) == 0:
            message.append("The username " + username + " does not exist.")
            message.append(
                " Please ensure you have entered the name correctly.")
            session["prev-page"] = request.url
            return render_template(
                "error.html", message=message,
                requestCount=get_connection_request_count())
        else:
            data = row[0]
            name, bio, gender, birthday, profile_picture = (
                data[0], data[1], data[2], data[3], data[4])

    # Award achievement ID 1 - Look at you if necessary
    if username == session["username"]:
        cur.execute(
            "SELECT * FROM CompleteAchievements "
            "WHERE (username=? AND achievement_ID=?);",
            (session["username"], 1))
        if cur.fetchone() is None:
            apply_achievement(session["username"], 1)

    # Award achievement ID 2 - Looking good if necessary
    if username != session["username"] and session["username"]:
        cur.execute(
            "SELECT * FROM CompleteAchievements "
            "WHERE (username=? AND achievement_ID=?);",
            (session["username"], 2))
        if cur.fetchone() is None:
            apply_achievement(session["username"], 2)

    # Gets account type.
    cur.execute(
        "SELECT type FROM "
        "ACCOUNTS WHERE username=?;", (username,))
    row = cur.fetchall()
    account_type = row[0][0]

    # Gets users degree.
    cur.execute(
        "SELECT degree FROM  "
        "Degree WHERE degreeId = (SELECT degree "
        "FROM UserProfile WHERE username=?);", (username,))
    row = cur.fetchone()
    degree = row[0]

    # Gets the user's hobbies.
    cur.execute("SELECT hobby FROM UserHobby WHERE username=?;",
                (username,))
    row = cur.fetchall()
    if len(row) > 0:
        hobbies = row

    # Gets the user's interests.
    cur.execute("SELECT interest FROM UserInterests WHERE username=?;",
                (username,))
    row = cur.fetchall()
    if len(row) > 0:
        interests = row

    # Gets the user's emails.
    cur.execute("SELECT email from ACCOUNTS WHERE username=?;",
                (username,))
    row = cur.fetchall()
    if len(row) > 0:
        email = row[0][0]

    # Gets the user's six rarest achievements.
    unlocked_achievements, locked_achievements = get_achievements(username)
    first_six = unlocked_achievements[0:min(6, len(unlocked_achievements))]

    # Gets the user's posts.
    if username == session["username"]:
        cur.execute(
            "SELECT * FROM POSTS WHERE username=?", (username,))
        sort_posts = cur.fetchall()
    else:
        connections = get_all_connections(username)
        count = 0
        for connection in connections:
            connections[count] = connection[0]
            count += 1
        if session["username"] in connections:
            close = is_close_friend(username)
            if close is True:
                cur.execute(
                    "SELECT * "
                    "FROM POSTS WHERE username=? AND privacy!='private'",
                    (username,))
                sort_posts = cur.fetchall()
            else:
                cur.execute(
                    "SELECT * FROM POSTS WHERE username=? "
                    "AND privacy!='private' AND privacy!='close'", (username,))
                sort_posts = cur.fetchall()
        else:
            cur.execute(
                "SELECT * FROM POSTS WHERE username=? AND privacy='public'",
                (username,))
            sort_posts = cur.fetchall()

    # Sort reverse chronologically
    sort_posts = sorted(sort_posts, key=lambda x: x[0], reverse=True)

    user_posts = {
        "UserPosts": []
    }

    for user_post in sort_posts:
        add = ""
        if len(user_post[2]) > 250:
            add = "..."

        if user_post[5] == "protected":
            privacy = "Friends only"
            icon = "user plus"
        elif user_post[5] == "close":
            privacy = "Close friends only"
            icon = "handshake outline"
        elif user_post[5] == "private":
            privacy = "Private"
            icon = "lock"
        else:
            privacy = str(user_post[5]).capitalize()
            icon = "users"

        time = datetime.strptime(user_post[4], '%Y-%m-%d').strftime('%d-%m-%y')
        user_posts["UserPosts"].append({
            "postId": user_post[0],
            "title": user_post[1],
            "profile_pic": "https://via.placeholder.com/600",
            "author": user_post[3],
            "account_type": user_post[6],
            "date_posted": time,
            "body": (user_post[2])[:250] + add,
            "privacy": privacy,
            "icon": icon
        })

    # Calculates the user's age based on their date of birth.
    datetime_object = datetime.strptime(birthday, "%Y-%m-%d")
    age = calculate_age(datetime_object)

    # Gets the connection type with the user to show their relationship.
    cur.execute(
        "SELECT * FROM CloseFriend WHERE (user1=? AND user2=?);",
        (session["username"], username))
    if cur.fetchone() is None:
        conn_type = get_connection_type(username)
    else:
        conn_type = "close"
    session["prev-page"] = request.url

    check_level_exists(username, conn)

    level_data = get_level(username)
    level = level_data[0]
    current_xp = level_data[1]
    xp_next_level = level_data[2]

    percentage_level = 100 * float(current_xp) / float(xp_next_level)
    progress_color = "green"
    if percentage_level < 75:
        progress_color = "orange"
    if percentage_level < 50:
        progress_color = "yellow"
    if percentage_level < 25:
        progress_color = "red"
    print(conn_type)

    return render_template("profile.html", username=username,
                           name=name, bio=bio, gender=gender,
                           birthday=birthday, profile_picture=profile_picture,
                           age=age, hobbies=hobbies, account_type=account_type,
                           interests=interests, degree=degree,
                           email=email, posts=user_posts, type=conn_type,
                           unlocked_achievements=first_six,
                           allUsernames=get_all_usernames(),
                           requestCount=get_connection_request_count(),
                           level=level, current_xp=int(current_xp),
                           xp_next_level=int(xp_next_level),
                           progress_color=progress_color)


@application.route("/edit-profile", methods=["GET", "POST"])
def edit_profile() -> object:
    """
    Updates the user's profile using info from the edit profile form.

    Returns:
        The updated profile page if the details provided were valid.
    """
    degrees = {
        "degrees": []
    }
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT birthday FROM UserProfile WHERE username=?",
            (session["username"],))
        dob = cur.fetchall()[0][0]
        cur.execute(
            "SELECT bio FROM UserProfile WHERE username=?",
            (session["username"],))
        bio = cur.fetchall()[0][0]

        # gets all possible degrees
        cur.execute(
            "SELECT * FROM Degree", )
        degree_list = cur.fetchall()
        for item in degree_list:
            degrees["degrees"].append({
                "degreeId": item[0],
                "degree": item[1]
            })

    # Renders the edit profile form if they navigated to this page.
    if request.method == "GET":
        return render_template("settings.html",
                               requestCount=get_connection_request_count(),
                               date=dob, bio=bio, degrees=degrees, errors=[])

    # Processes the form if they updated their profile using the form.
    if request.method == "POST":
        # Ensures that users can only edit their own profile.
        username = session["username"]
        # Gets the input data from the edit profile details form.
        bio = request.form.get("bio_input")

        # Award achievement ID 11 - Describe yourself if necessary
        if bio != "Change your bio in the settings." and bio != "":
            cur.execute(
                "SELECT * FROM CompleteAchievements "
                "WHERE (username=? AND achievement_ID=?);",
                (session["username"], 11))
            if cur.fetchone() is None:
                apply_achievement(username, 11)

        gender = request.form.get("gender_input")
        dob_input = request.form.get("dob_input")
        dob = datetime.strptime(dob_input, "%Y-%m-%d").strftime("%Y-%m-%d")
        hobbies_input = request.form.get("hobbies")
        interests_input = request.form.get("interests")
        degree = request.form.get("degree_input")
        # Gets the individual hobbies and interests, then formats them.
        hobbies_unformatted = hobbies_input.split(",")
        hobbies = [hobby.lower() for hobby in hobbies_unformatted]
        interests_unformatted = interests_input.split(",")
        interests = [interest.lower() for interest in interests_unformatted]

        # Connects to the database to perform validation.
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()

            # Validates user profile details and uploaded image.
            valid, message = validate_edit_profile(bio, gender, dob, hobbies,
                                                   interests)
            if valid is True:
                file = request.files["file"]
                valid, message, file_name_hashed = validate_profile_pic(file)

            # Updates the user profile if details are valid.
            if valid is True:
                # Updates the bio, gender, and birthday.
                if file_name_hashed:
                    cur.execute(
                        "UPDATE UserProfile SET bio=?, gender=?, birthday=?, "
                        "profilepicture=?, degree=? WHERE username=?;",
                        (bio, gender, dob,
                         application.config[
                             'UPLOAD_FOLDER'] + "/avatars/" + file_name_hashed
                         + ".jpg", degree, username,))
                else:
                    cur.execute(
                        "UPDATE UserProfile SET bio=?, gender=?, birthday=?, "
                        "degree=? WHERE username=?;",
                        (bio, gender, dob, degree, username,))

                # Inserts new hobbies and interests into the database if the
                # user made a new input.
                if hobbies != [""]:
                    for hobby in hobbies:
                        cur.execute("SELECT hobby FROM UserHobby WHERE "
                                    "username=? AND hobby=?;",
                                    (username, hobby,))
                        if cur.fetchone() is None:
                            cur.execute("INSERT INTO UserHobby (username, "
                                        "hobby) VALUES (?, ?);",
                                        (username, hobby,))
                if interests != [""]:
                    for interest in interests:
                        cur.execute("SELECT interest FROM UserInterests WHERE "
                                    "username=? AND interest=?;",
                                    (username, interest,))
                        if cur.fetchone() is None:
                            cur.execute("INSERT INTO UserInterests "
                                        "(username, interest) VALUES (?, ?);",
                                        (username, interest,))

                conn.commit()
                return redirect("/profile")
            # Displays error message(s) stating why their details are invalid.
            else:
                session["error"] = message
                return render_template(
                    "settings.html", errors=message,
                    requestCount=get_connection_request_count(),
                    allUsernames=get_all_usernames(), degrees=degrees,
                    date=dob, bio=bio)


@application.route("/logout", methods=["GET"])
def logout():
    """
    Clears the user's session if they are logged in.

    Returns:
        The web page for logging in if the user logged out of an account.
    """
    if "username" in session:
        session.clear()
        session["prev-page"] = request.url
        return render_template("login.html")
    return redirect("/")


def allowed_file(filename) -> bool:
    """
    Checks if the file is an allowed type.

    Args:
        filename: The name of the file uploaded by the user.

    Returns:
        Whether the file is allowed or not (True/False).
    """
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg", "gif"}


def apply_achievement(username: str, achievement_id: int):
    """
    Marks an achievement as unlocked by the user.

    Args:
        username: The user who unlocked the achievement.
        achievement_id: The ID of the achievement unlocked.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO CompleteAchievements "
            "(username, achievement_ID, date_completed) VALUES (?, ?, ?);",
            (username, achievement_id, date.today()))
        conn.commit()
        cur.execute(
            "SELECT xp_value FROM Achievements WHERE achievement_ID=?;",
            (achievement_id,))
        xp = cur.fetchone()[0]
        check_level_exists(username, conn)
        cur.execute(
            "UPDATE UserLevel "
            "SET experience = experience + ? "
            "WHERE username=?;",
            (xp, username))
        conn.commit()


def calculate_age(born):
    """
    Calculates the user's current age based on their date of birth.

    Args:
        born: The user's date of birth.

    Returns:
        The age of the user in years.
    """
    today = date.today()
    return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day))


def check_level_exists(username: str, conn):
    """
    Checks that a user has a record in the database for their level.

    Args:
        username: The username of the user to check.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM UserLevel WHERE username=?;", (username,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO UserLevel (username, experience) VALUES (?, ?);",
            (username, 0))
        conn.commit()


def get_achievements(username: str) -> Tuple[object, object]:
    """
    Gets unlocked and locked achievements for the user.

    Returns:
        A list of unlocked and locked achievements and their details.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # Gets unlocked achievements, sorted by XP descending.
        cur.execute(
            "SELECT description, icon, rarity, xp_value, achievement_name "
            "FROM CompleteAchievements "
            "INNER JOIN Achievements ON CompleteAchievements"
            ".achievement_ID = Achievements.achievement_ID "
            "WHERE username=?;",
            (username,))
        unlocked_achievements = cur.fetchall()
        unlocked_achievements.sort(key=lambda x: x[3], reverse=True)

        # Get locked achievements, sorted by XP ascending.
        cur.execute(
            "SELECT description, icon, rarity, xp_value, achievement_name "
            "FROM Achievements")
        all_achievements = cur.fetchall()
        locked_achievements = list(
            set(all_achievements) - set(unlocked_achievements))
        locked_achievements.sort(key=lambda x: x[3])

    return unlocked_achievements, locked_achievements


def get_all_connections(username) -> list:
    """
    Gets a list of all usernames that are connected to the logged in user.

    Returns:
        A list of all usernames that are connected to the logged in user.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user2 FROM Connection "
            "WHERE user1=? AND connection_type='connected' UNION ALL "
            "SELECT user1 FROM Connection "
            "WHERE user2=? AND connection_type='connected'",
            (username, username)
        )
        cons = cur.fetchall()

        return cons


def get_all_usernames() -> list:
    """
    Gets a list of all usernames that are registered.

    Returns:
        A list of all usernames that have been registered.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT username FROM Accounts")

        row = cur.fetchall()

        return row


def get_connection_request_count() -> int:
    """
    Counts number of pending connection requests for a user.

    Returns:
        The number of pending connection requests for a user.
    """

    if "username" not in session:
        return 0

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM Connection WHERE user2=? AND "
            "connection_type='request';",
            (session["username"],))
        return len(list(cur.fetchall()))


def get_connection_type(username: str):
    """
    Checks what type of connection the user has with the specified user.

    Args:
        username: The user to check the connection type with.

    Returns:
        The type of connection with the specified user.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT connection_type FROM Connection WHERE user1=? "
            "AND user2=?", (session["username"], username,))
        conn.commit()

        # Checks if there is a connection between the two users.
        row = cur.fetchone()
        if row is not None:
            return row[0]
        else:
            cur.execute(
                "SELECT connection_type FROM Connection WHERE user1=? AND "
                "user2=?", (username, session["username"],))
            conn.commit()
            row = cur.fetchone()
            if row is not None:
                if row[0] == "connected":
                    return row[0]
                return "incoming"
            else:
                return None


def get_level(username) -> List[int]:
    """
    Gets the current user experience points, the experience points
    for the next level and the user's current level from the database.

    Args:
        username: The username of the user logged in.

    Returns:
        The user's level, XP, and XP to reach the next level.
    """
    level = 1
    xp_next_level = 100
    xp_increase_per_level = 15

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        check_level_exists(username, conn)
        # Get user experience
        cur.execute(
            "SELECT experience FROM "
            "UserLevel WHERE username=?;", (username,))
        row = cur.fetchone()

        xp = int(row[0])
        while xp >= xp_next_level:
            level += 1
            xp -= xp_next_level
            xp_next_level += xp_increase_per_level

        return [level, xp, xp_next_level]


def get_profile_picture(username: str) -> str:
    """
    Gets the profile picture of a user.

    Args:
        username: The username of the user's profile picture.

    Returns:
        The profile picture of the user.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT profilepicture FROM UserProfile WHERE username=?;",
            (username,)
        )
        row = cur.fetchone()

    return row[0]


def is_close_friend(username) -> bool:
    """
    Gets whether the selected user has the logged in as a close friend.

    Returns:
        Whether the user is a close friend of the user (True/False).
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM CloseFriend WHERE (user1=? AND user2=?);",
            (session["username"], username)
        )
        row = cur.fetchone()
        if row is not None:
            return True

    return False


def validate_edit_profile(
        bio: str, gender: str, dob: str,
        hobbies: list, interests: list) -> Tuple[bool, List[str]]:
    """
    Validates the details in the profile editing form.

    Args:
        bio: The bio input by the user in the form.
        gender: The gender input selected by the user in the form.
        dob: The date of birth input selected by the user in the form.
        hobbies: The list of hobbies from the form.
        interests: The list of interests from the form.
    Returns:
        Whether profile editing was valid, and the error message(s) if not.
    """
    # Editing profile remains valid as long as it isn't caught by any checks.
    # If not, error messages will be provided to the user.
    valid = True
    message = []

    # Checks that the bio has a maximum of 160 characters.
    if len(bio) > 160:
        valid = False
        message.append("Bio must not exceed 160 characters!")

    # Checks that the gender is male, female, or other.
    if gender not in ["Male", "Female", "Other"]:
        valid = False
        message.append("Gender must be male, female, or other!")

    # Only performs check if a new date of birth was entered.
    if dob != "":
        # Converts date string to datetime.
        dob = datetime.strptime(dob, "%Y-%m-%d")
        # Checks that date of birth is a past date.
        if datetime.today() < dob:
            valid = False
            message.append("Date of birth must be a past date!")

    # Checks that each hobby has a maximum of 24 characters.
    for hobby in hobbies:
        if len(hobby) > 24:
            valid = False
            message.append("Hobbies must not exceed 24 characters!")
            break

    # Checks that each interest has a maximum of 24 characters.
    for interest in interests:
        if len(interest) > 24:
            valid = False
            message.append("Interests must not exceed 24 characters!")
            break

    return valid, message


def validate_registration(
        cur, username: str, full_name: str, password: str,
        password_confirm: str,
        email: str, terms: str) -> Tuple[bool, List[str]]:
    """
    Validates the registration details to ensure that the email address is
    valid, and that the passwords in the form match.

    Args:
        cur: Cursor for the SQLite database.
        username: The username input by the user in the form.
        full_name: The full name input by the user in the form.
        password: The password input by the user in the form.
        password_confirm: The password confirmation input by the user in the
            form.
        email: The email address input by the user in the form.
        terms: The terms and conditions input checkbox.
    Returns:
        Whether the registration was valid, and the error message(s) if not.
    """
    # Registration remains valid as long as it isn't caught by any checks. If
    # not, error messages will be provided to the user.
    valid = True
    message = []

    # Checks that there are no null inputs.
    if (username == "" or full_name == "" or password == "" or
            password_confirm == "" or email == ""):
        message.append("Not all fields have been filled in!")
        valid = False

    # Checks that the username only contains valid characters.
    if username.isalnum() is False:
        message.append("Username must only contain letters and numbers!")
        valid = False

    # Checks that the username hasn't already been registered.
    cur.execute("SELECT * FROM Accounts WHERE username=?;", (username,))
    if cur.fetchone() is not None:
        message.append("Username has already been registered!")
        valid = False

    # Checks that the full name doesn't exceed 40 characters.
    if len(full_name) > 40:
        message.append("Full name exceeds 40 characters!")
        valid = False

    # Checks that the full name only contains valid characters.
    if not all(x.isalpha() or x.isspace() for x in full_name):
        message.append("Full name must only contain letters and spaces!")
        valid = False

    # Checks that the email hasn't already been registered.
    cur.execute("SELECT * FROM Accounts WHERE email=?;", (email,))
    if cur.fetchone() is not None:
        message.append("Email has already been registered!")
        valid = False

    # Checks that the email address has the correct format, checks whether it
    # exists, and isn't a blacklist email.
    try:
        valid_email = validate_email(email)
        # Updates with the normalised form of the email address.
        email = valid_email.email
    except EmailNotValidError:
        message.append("Email is invalid!")
        valid = False

    # If the format is valid, checks that the email address has the
    # University of Exeter domain.
    if re.search("@.*", email) is not None:
        domain = re.search("@.*", email).group()
        if domain != "@exeter.ac.uk":
            valid = False
            message.append(
                "Email address does not belong to University of Exeter!")

    # Checks that the password has a minimum length of 8 characters, and at
    # least one number.
    if (len(password) <= 7 or any(
            char.isdigit() for char in password) is False):
        message.append("Password does not meet requirements! It must contain "
                       "at least eight characters, including at least one "
                       "number.")
        valid = False

    # Checks that the passwords match.
    if password != password_confirm:
        message.append("Passwords do not match!")
        valid = False

    # Checks that the terms of service has been ticked.
    if terms is None:
        message.append("You must accept the terms of service!")
        valid = False

    return valid, message


def validate_profile_pic(file) -> Tuple[bool, List[str], str]:
    """
    Validates the file to check that it's a valid image.

    Args:
        file: The he file uploaded by the user.

    Returns:
        Whether the file uploaded is a valid image, and any error messages.
    """
    valid = True
    message = []
    file_name_hashed = ""

    # Hashes the name of the file and resizes it.
    if allowed_file(file.filename):
        secure_filename(file.filename)
        file_name_hashed = str(uuid.uuid4())
        file_path = os.path.join(
            "." + application.config["UPLOAD_FOLDER"] + "//avatars",
            file_name_hashed)
        im = Image.open(file)
        im = im.resize((400, 400))
        im = im.convert("RGB")
        im.save(file_path + ".jpg")
    elif file:
        valid = False
        message.append("Your file must be an image.")

    return valid, message, file_name_hashed


if __name__ == "__main__":
    application.run(debug=True)
