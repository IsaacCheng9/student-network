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
application.config['UPLOAD_FOLDER'] = '/static/images//avatars'


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

                    # Award achievement ID 17 if necessary
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

                    # Award achievement ID 5 - Popular if necessary
                    cur.execute(
                        "SELECT * FROM CompleteAchievements "
                        "WHERE (username=? AND achievement_ID=?);",
                        (session["username"], 5))
                    if cur.fetchone() is None:
                        cur.execute(
                            "SELECT * FROM Connection "
                            "WHERE (user1=? OR user2=?);",
                            (session["username"], session["username"]))
                        if len(cur.fetchall()) >= 10:
                            apply_achievement(session["username"], 5)

                    # Award achievement ID 5 to connected user
                    cur.execute(
                        "SELECT * FROM CompleteAchievements "
                        "WHERE (username=? AND achievement_ID=?);",
                        (session["username"], 5))
                    if cur.fetchone() is None:
                        cur.execute(
                            "SELECT * FROM Connection "
                            "WHERE (user1=? OR user2=?);",
                            (username, username))
                        if len(cur.fetchall()) >= 10:
                            apply_achievement(username, 5)

                    # Award achievement ID 6 - Centre of Attention if necessary
                    cur.execute(
                        "SELECT * FROM CompleteAchievements "
                        "WHERE (username=? AND achievement_ID=?);",
                        (session["username"], 6))
                    if cur.fetchone() is None:
                        cur.execute(
                            "SELECT * FROM Connection "
                            "WHERE (user1=? OR user2=?);",
                            (session["username"], session["username"]))
                        if len(cur.fetchall()) >= 100:
                            apply_achievement(session["username"], 6)

                    # Award achievement ID 6 to connected user
                    cur.execute(
                        "SELECT * FROM CompleteAchievements "
                        "WHERE (username=? AND achievement_ID=?);",
                        (username, 6))
                    if cur.fetchone() is None:
                        cur.execute(
                            "SELECT * FROM Connection "
                            "WHERE (user1=? OR user2=?);",
                            (username, username))
                        if len(cur.fetchall()) >= 100:
                            apply_achievement(username, 6)
    else:
        session["add"] = "You can't connect with yourself!"

    return redirect(session["prev-page"])


def apply_achievement(username: str, achievement_ID: int):
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO CompleteAchievements "
            "(username, achievement_ID, date_completed) VALUES (?, ?, ?);",
            (username, achievement_ID, date.today()))
        conn.commit()
        cur.execute(
            "SELECT xp_value FROM Achievements WHERE achievement_ID=?;",
            (achievement_ID,))
        xp = cur.fetchone()[0]
        cur.execute(
            "SELECT * FROM UserLevel WHERE username=?;", (username,))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO UserLevel (username, experience) VALUES (?,?);",
                (username, 0))
        conn.commit()
        cur.execute(
            "UPDATE UserLevel "
            "SET experience = experience + ? "
            "WHERE username=?;",
            (xp, username))
        conn.commit()


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

    return redirect(session["prev-page"])


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

    session["prev-page"] = request.url

    return render_template("request.html", requests=requests, avatars=avatars,
                           allUsernames=get_all_usernames(),
                           requestCount=get_connection_request_count())


@application.route("/terms", methods=["GET", "POST"])
def terms_page():
    """
    Renders the terms and conditions page.

    Returns:
        The web page for T&Cs, or redirection back to register page.
    """
    if request.method == "GET":
        session["prev-page"] = request.url
        return render_template("terms.html")
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
                               errors=errors)


@application.route("/register", methods=["POST"])
def register_submit() -> object:
    """
    Registers an account using the user's input from the registration form.

    Returns:
        The updated web page based on whether the details provided were valid.
    """
    # Obtains user input from the account registration form.
    username = request.form["username_input"].lower()
    fullname = request.form["fullname_input"]
    password = request.form["psw_input"]
    password_confirm = request.form["psw_input_check"]
    email = request.form["email_input"]
    terms = request.form.get("terms")

    # Connects to the database to perform validation.
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        valid, message = validate_registration(cur, username, fullname,
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
                    username, fullname, "Change your bio in the settings.",
                    "Male", date.today(), "/static/images/default-pfp.jpg",))

            cur.execute(
                "INSERT INTO Userlevel (username, experience) "
                "VALUES (?, 0);", (username,))

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
    Loads a post and it's comments

    Returns:
        Redirection to their profile if they're logged in.
    """
    comments = {"comments": []}
    message = []
    author = ""
    i = 0

    session["prev-page"] = request.url

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # Gets user from database using username.
        cur.execute(
            "SELECT title, body, username, date, account_type, likes "
            "FROM POSTS WHERE postId=?;", (post_id,))
        row = cur.fetchall()
        if len(row) == 0:
            message.append("This post does not exist.")
            message.append(
                " Please ensure you have entered the name correctly.")
            session["prev-page"] = request.url
            return render_template("error.html", message=message,
                                   requestCount=get_connection_request_count(),
                                   allUsernames=get_all_usernames())
        else:
            data = row[0]
            title, body, username, date, account_type, likes = (
                data[0], data[1],
                data[2], data[3],
                data[4], data[5])
            cur.execute(
                "SELECT *"
                "FROM Comments WHERE postId=?;", (post_id,))
            row = cur.fetchall()
            if len(row) == 0:
                return render_template(
                    "post_page.html", author=author, postId=post_id,
                    title=title, body=body, username=username, date=date,
                    likes=likes, accountType=account_type, comments=None,
                    requestCount=get_connection_request_count(),
                    allUsernames=get_all_usernames())
            for comment in row:
                if i == 20:
                    break
                comments["comments"].append({
                    "commentId": comment[0],
                    "username": comment[1],
                    "body": comment[2],
                    "date": comment[3],
                })
                i += 1
            
            return render_template(
                "post_page.html", author=author, postId=post_id, title=title,
                body=body, username=username, date=date, likes=likes,
                accountType=account_type, comments=comments,
                requestCount=get_connection_request_count(),
                allUsernames=get_all_usernames())


@application.route("/feed", methods=["GET"])
def feed():
    """
    Checks user is logged in before viewing their feed page.

    Returns:
        Redirection to their feed if they're logged in.
    """
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
            #account type differentiation in posts db
            for post in reversed(row):
                if i == 20:
                    break
                add = ""
                if len(post[2]) > 250:
                    add = "..."
                time = datetime.strptime(post[4], '%Y-%m-%d').strftime(
                    '%d-%m-%y')
                
                #Get account type 
                cur.execute( "SELECT type "
                            "FROM ACCOUNTS WHERE username=? ",
                            (post[3],))
                accounts = cur.fetchone()
                account_type = accounts[0]
                all_posts["AllPosts"].append({
                    "postId": post[0],
                    "title": post[1],
                    "profile_pic": "https://via.placeholder.com/600",
                    "author": post[3],
                    "account_type": account_type,
                    "date_posted": time,
                    "body": (post[2])[:250] + add
                })
                i += 1
        

        if "error" in session:
            errors = []
            errors = session["error"]
            session.pop("error", None)

            return render_template("feed.html", posts=all_posts,
                    requestCount=get_connection_request_count(),
                    allUsernames=get_all_usernames(),errors = errors)
        else: 
            return render_template("feed.html", posts=all_posts,
                                requestCount=get_connection_request_count(),
                                allUsernames=get_all_usernames(),)
    else:
        return redirect("/login")


@application.route("/submit_post", methods=["POST"])
def submit_post():
    """
    Submit post on social wall to database.

    Returns:
        Updated feed with new post added
    """
    try:
        post_title = request.form["post_title"]
        post_body = request.form["post_text"]
        if post_title != "":
            with sqlite3.connect("database.db") as conn:
                cur = conn.cursor()
                # TODO: 6th value in table is privacy setting and 7th is account type.
                # Currently is default - public/student but no functionality
                cur.execute("INSERT INTO POSTS (title, body, username) "
                            "VALUES (?, ?, ?);",
                            (post_title, post_body, session["username"]))
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
                    print(results)
                    print(len(results))
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
                    print(results)
                    print(len(results))
                    if len(results) >= 20:
                        apply_achievement(session["username"], 9)
        else:
            #Prints error message missing title on top of page
            session["error"]=["Missing Title!"]
    except:
        conn.rollback()
        #Prints error message in case post couldnt be created
        session["error"].append(["Post could not be created"])
    finally:
        return redirect("/feed")


@application.route("/like_post", methods=["POST"])
def like_post():
    """
    Add post like  to database.

    Returns:
        Updated post with like added
    """
    likes = 0
    row = []
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

            # get current total number of  current likes
            cur.execute("SELECT likes FROM POSTS"
                        " WHERE postId=?;", (post_id,))
            row = cur.fetchone()

            likes = row[0] + 1
            cur.execute("UPDATE POSTS SET likes=? "
                        " WHERE postId=? ;", (likes, post_id,))
            conn.commit()

            # Check how many posts user has liked
            cur.execute("SELECT COUNT(postId) FROM UserLikes"
                        " WHERE username=? ;", (session["username"],))
            row = cur.fetchone()
            if row == 1:
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (session["username"], 20))
                if cur.fetchone() is None:
                    apply_achievement(session["username"], 20)
            elif row == 5:
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (session["username"], 23))
                if cur.fetchone() is None:
                    apply_achievement(session["username"], 23)
            elif row == 100:
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (session["username"], 24))
                if cur.fetchone() is None:
                    apply_achievement(session["username"], 24)
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
    if comment_body != "":
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
    Delete post from database.

    Returns:
        Feed page
    """
    post_id = request.form["postId"]
    message = []
    try:
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
    except:
        conn.rollback()
    finally:
        message.append("Comment has been deleted successfully.")
        return render_template("error.html", message=message,
                               requestCount=get_connection_request_count(),
                               allUsernames=get_all_usernames())


@application.route("/delete_comment", methods=["POST"])
def delete_comment():
    """
    Delete comment from database.

    Returns:
        post_page
    """
    message = []
    post_id = request.form["postId"]
    comment_id = request.form["commentId"]
    try:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Comments WHERE commentId=? ",
                        (comment_id,))
            row = cur.fetchone()
            # check the post exists in database
            if row[0] is None:
                message.append("Comment does not exist.")
                return render_template(
                    "error.html", message=message,
                    requestCount=get_connection_request_count(),
                    allUsernames=get_all_usernames())
            else:
                cur.execute("DELETE FROM Comments WHERE commentId =? ",
                            (comment_id,))
                conn.commit()
    except:
        conn.rollback()
        message.append("The comment could not be deleted.")
        return render_template("error.html", message=message,
                               requestCount=get_connection_request_count(),
                               allUsernames=get_all_usernames())
    finally:
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
    name = ""
    bio = ""
    gender = ""
    birthday = ""
    profile_picture = ""
    email = ""
    hobbies = []
    interests = []
    account_type = ""
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
            return render_template("error.html", message=message,
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
    
    set = []
    if username == session["username"]:
        # TODO: store all the users posts in a json file
        cur.execute(
            "SELECT * "
            "FROM POSTS WHERE username=?", (username,))
        set = cur.fetchall()
    else:
        connections = get_all_connections(username)
        count = 0
        for connection in connections:
            connections[count] = connection[0]
            count += 1
        if session["username"] in connections:
            close = am_close_friend(username)
            if close is True:
                cur.execute(
                    "SELECT * "
                    "FROM POSTS WHERE username=? AND privacy!='private'",
                    (username,))
                set = cur.fetchall()
            else:
                cur.execute(
                    "SELECT * "
                    "FROM POSTS WHERE username=? "
                    "AND privacy!='private' AND privacy!='close'", (username,))
                set = cur.fetchall()
        else:
            cur.execute(
                "SELECT * "
                "FROM POSTS WHERE username=? AND privacy='public'",
                (username,))
            set = cur.fetchall()


    # Sort reverse chronologically
    set = sorted(set, key=lambda x: x[0], reverse=True)

    user_posts = {
        "UserPosts": []
    }
    i=0

    for post in set:
        add = ""
        if len(post[2]) > 250:
            add = "..."
        time = datetime.strptime(post[4], '%Y-%m-%d').strftime('%d-%m-%y')
        user_posts["UserPosts"].append({
            "postId": post[0],
            "title": post[1],
            "profile_pic": "https://via.placeholder.com/600",
            "author": post[3],
            "date_posted": time,
            "body": (post[2])[:250] + add
        })
        i += 1

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

    level_data = get_level(username)
    level = level_data[0]
    current_xp = level_data[1]
    xp_next_level = level_data[2]

    percentage_level = 100 * float(current_xp) / float(xp_next_level)
    progress_color = "green"
    if percentage_level < 25:
        progress_color = "yellow"
    if percentage_level < 50:
        progress_color = "orange"
    if percentage_level < 75:
        progress_color = "red"
    print(conn_type)
    return render_template("profile.html", username=username,
                           name=name, bio=bio, gender=gender,
                           birthday=birthday, profile_picture=profile_picture,
                           age=age, hobbies=hobbies, account_type=account_type,
                           interests=interests,
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
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT birthday FROM UserProfile WHERE username=?",
            (session["username"],))
        date = cur.fetchall()[0][0]
        cur.execute(
            "SELECT bio FROM UserProfile WHERE username=?",
            (session["username"],))
        bio = cur.fetchall()[0][0]

    # Renders the edit profile form if they navigated to this page.
    if request.method == "GET":
        return render_template("settings.html",
                               requestCount=get_connection_request_count(),
                               date=date, bio=bio, errors=[])

    # Processes the form if they updated their profile using the form.
    if request.method == "POST":
        # Ensures that users can only edit their own profile.
        username = session["username"]

        # Gets the input data from the edit profile details form.
        bio = request.form.get("bio_input")
        gender = request.form.get("gender_input")
        dob_input = request.form.get("dob_input")
        dob = datetime.strptime(dob_input, "%Y-%m-%d").strftime("%Y-%m-%d")
        hobbies_input = request.form.get("hobbies")
        interests_input = request.form.get("interests")

        # Gets the individual hobbies, and formats them.
        hobbies_unformatted = hobbies_input.split(",")
        hobbies = [hobby.lower() for hobby in hobbies_unformatted]
        # Gets the individual interests, and formats them.
        interests_unformatted = interests_input.split(",")
        interests = [interest.lower() for interest in interests_unformatted]
        # Connects to the database to perform validation.
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            # Applies changes to the user's profile details on the
            # database if valid.
            valid, message, filename = validate_edit_profile(bio, gender, dob,
                                                             hobbies,
                                                             interests)
            # Updates the user profile if details are valid.
            if valid is True:
                # Updates the bio, gender, and birthday.
                if filename:
                    cur.execute(
                        "UPDATE UserProfile SET bio=?, gender=?, birthday=?, "
                        "profilepicture=? WHERE username=?;",
                        (bio, gender, dob,
                         application.config['UPLOAD_FOLDER'] + "\\" + filename
                         + ".jpg", username,))
                else:
                    cur.execute(
                        "UPDATE UserProfile SET bio=?, gender=?, birthday=?"
                        "WHERE username=?;",
                        (bio, gender, dob,
                         username,))
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
                print(message)
                return render_template(
                    "settings.html", errors=message,
                    requestCount=get_connection_request_count(),
                    allUsernames=get_all_usernames(), date=date, bio=bio)


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
        return render_template("login.html",)
    return redirect("/")


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
        message.append("Full Name must only contain letters, numbers and"
                       " spaces!")
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

    # Checks that the password has a minimum length of 6 characters, and at
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


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


def validate_edit_profile(
        bio: str, gender: str, dob: str,
        hobbies: list, interests: list) -> Tuple[bool, List[str], str]:
    """
    Validates the details in the profile editing form.

    Args:
        bio: The bio input by the user in the form.
        gender: The gender input selected by the user in the form.
        dob: The date of birth input selected by the user in the form.
        profile_pic: The profile picture uploaded by the user in the form.
        hobbies: The list of hobbies from the form.
        interests: The list of interests from the form.
    Returns:
        Whether profile editing was valid, and the error message(s) if not.
    """
    # Editing profile remains valid as long as it isn't caught by any checks.
    # If not, error messages will be provided to the user.
    valid = True
    message = []
    new_filename = ''
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

    # Checks that the bio has a maximum of 160 characters.
    if len(bio) > 160:
        valid = False

        message.append("Bio must not exceed 160 characters!")

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

    if valid is True:
        file = request.files['file']
        print(file.filename)
        # if user does not select file, browser also
        # submit an empty part without filename
        if allowed_file(file.filename):
            secure_filename(file.filename)
            new_filename = str(uuid.uuid4())

            filepath = os.path.join("." + application.config['UPLOAD_FOLDER'],
                                    new_filename)

            im = Image.open(file)
            im = im.resize((400, 400))
            im = im.convert("RGB")
            im.save(filepath + ".jpg")

        elif file:
            valid = False
            message.append("Your file needs to be an image")

    print(valid)
    return valid, message, new_filename


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
        set = cur.fetchall()

        return set


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


def am_close_friend(username) -> bool:
    """
    Gets whether the selected user has the logged in as a close friend

    Returns:
        True if logged in is a close friend, false if not
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM CloseFriend WHERE (user1=? AND user2=?);",
            (username, session["username"])
        )
        row = cur.fetchone()
        if row is not None:
            return True
        return False


def get_level(username) -> List[int]:
    """
    gets the current user experience points, the experience points
    for the next level and the user's current level from the database

    Args:
        username: username of the user logged in

    Returns:
        level
        current xp
        xp next level
    """
    level = 1
    current_xp = 0
    xp_next_level = 100
    message = []

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # Get user experience
        cur.execute(
            "SELECT experience FROM "
            "UserLevel WHERE username=?;", (username,))
        row = cur.fetchall()
        if len(row) == 0:
            message.append("Problem with getting level")
            session["prev-page"] = request.url
            return render_template("error.html", message=message, 
                                    requestCount=get_connection_request_count())
        else:
            data = row[0]
            current_xp = data[0]
            cur.execute(
                "SELECT level, experience FROM "
                "Levels WHERE  experience > ?;", (current_xp,))
            row = cur.fetchone()
            if row is None:
                cur.execute("INSERT INTO Levels"
                            "VALUES( (1+(SELECT MAX(level)FROM Levels)),"
                            "(50*(SELECT MAX(level)FROM Levels)"
                            "+(SELECT MAX(experience)FROM Levels)))")
                cur.execute(
                    "SELECT level, experience FROM "
                    "Levels WHERE  experience > ?;", (current_xp,))
                row = cur.fetchone()
            level = row[0]
            xp_next_level = row[1]
            return [level, current_xp, xp_next_level]


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
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM Connection WHERE user2=? AND "
            "connection_type='request';",
            (session["username"],))

        return len(list(cur.fetchall()))


if __name__ == "__main__":
    application.run(debug=True)
