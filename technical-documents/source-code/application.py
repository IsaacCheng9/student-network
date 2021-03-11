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
from random import sample
from string import capwords
from typing import Tuple, List
from urllib.parse import parse_qs
from urllib.parse import urlparse

from PIL import Image
from email_validator import validate_email, EmailNotValidError
from flask import Flask, render_template, request, redirect, session, jsonify
from passlib.hash import sha256_crypt
from werkzeug.utils import secure_filename

application = Flask(__name__)
application.secret_key = ("\xfd{H\xe5 <\x95\xf9\xe3\x96.5\xd1\x01O <!\xd5\""
                          "xa2\xa0\x9fR\xa1\xa8")
application.url_map.strict_slashes = False
application.config["UPLOAD_FOLDER"] = "/static/images"


@application.route("/", methods=["GET"])
def index_page() -> object:
    """
    Renders the feed page if the user is logged in.

    Returns:
        The web page for user login.
    """
    if "username" in session:
        return redirect("/profile")
    else:
        session["prev-page"] = request.url
        return render_template("home_page.html")


@application.route("/login", methods=["GET"])
def login_page() -> object:
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


@application.route("/unblock_user/<username>", methods=["GET", "POST"])
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
        cur.execute("SELECT * FROM Accounts WHERE username=?;",
                    (username,))
        if cur.fetchone() is not None:
            if get_connection_type(username) == "block":
                if username != session['username']:
                    cur.execute(
                        "DELETE FROM Connection WHERE (user1=? AND user2=?);",
                        (session["username"], username))
                    conn.commit()
    return redirect(session["prev-page"])


@application.route("/members", methods=["GET"])
def members() -> object:
    """
    Displays all members registered to the student network.

    Returns:
        The web page for displaying members.
    """
    session["prev-page"] = request.url
    return render_template("members.html",
                           requestCount=get_connection_request_count())


@application.route("/quizzes", methods=["GET"])
def quizzes() -> object:
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT quiz_id, date_created, author, quiz_name FROM Quiz")

        row = cur.fetchall()

        quiz_posts = sorted(row, key=lambda x: x[0], reverse=True)


    # Displays any error messages.
    if "error" in session:
        errors = session["error"]
        session.pop("error", None)
        return render_template("quizzes.html",
                               requestCount=get_connection_request_count(),
                               quizzes=quiz_posts, errors=errors)
    else:
        return render_template("quizzes.html",
                               requestCount=get_connection_request_count(),
                               quizzes=quiz_posts)


@application.route("/quiz/<quiz_id>", methods=["GET", "POST"])
def quiz(quiz_id: int) -> object:
    # Gets the quiz details from the database.
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT quiz_name, date_created, author, question_1, "
            "question_1_ans_1, question_1_ans_2, question_1_ans_3, "
            "question_1_ans_4, question_2, question_2_ans_1, "
            "question_2_ans_2, question_2_ans_3, question_2_ans_4, "
            "question_3, question_3_ans_1, question_3_ans_2, "
            "question_3_ans_3, question_3_ans_4, question_4, "
            "question_4_ans_1, question_4_ans_2, question_4_ans_3, "
            "question_4_ans_4, question_5, question_5_ans_1, "
            "question_5_ans_2, question_5_ans_3, question_5_ans_4, privacy "
            "FROM Quiz WHERE quiz_id=?;", (quiz_id,))
        quiz_details = cur.fetchall()
        quiz_name = quiz_details[0][0]
        question_1 = quiz_details[0][3]
        question_1_options = sample(
            [quiz_details[0][4], quiz_details[0][5],
             quiz_details[0][6], quiz_details[0][7]], 4)
        question_2 = quiz_details[0][8]
        question_2_options = sample(
            [quiz_details[0][9], quiz_details[0][10],
             quiz_details[0][11], quiz_details[0][12]], 4)
        question_3 = quiz_details[0][13]
        question_3_options = sample(
            [quiz_details[0][14], quiz_details[0][15],
             quiz_details[0][16], quiz_details[0][17]], 4)
        question_4 = quiz_details[0][18]
        question_4_options = sample(
            [quiz_details[0][19], quiz_details[0][20],
             quiz_details[0][21], quiz_details[0][22]], 4)
        question_5 = quiz_details[0][23]
        question_5_options = sample(
            [quiz_details[0][24], quiz_details[0][25],
             quiz_details[0][26], quiz_details[0][27]], 4)

        # Gets a list of questions and answers to pass to the web page.
        questions = [question_1, question_2, question_3, question_4,
                     question_5]
        answers = [question_1_options, question_2_options,
                   question_3_options, question_4_options,
                   question_5_options]

    if request.method == "GET":
        return render_template("quiz.html",
                               requestCount=get_connection_request_count(),
                               quiz_name=quiz_name, quiz_id=quiz_id,
                               questions=questions, answers=answers)

    elif request.method == "POST":
        score = 0
        # Gets the answers selected by the user.
        user_answers = [request.form.get("userAnswer0"),
                        request.form.get("userAnswer1"),
                        request.form.get("userAnswer2"),
                        request.form.get("userAnswer3"),
                        request.form.get("userAnswer4")]

        # Displays an error message if they have not answered all questions.
        if any(user_answers) == "":
            session["error"] = "You have not answered all the questions!"
            return redirect(session["prev-page"])
        else:
            question_feedback = []
            for i in range(5):
                correct_answer = quiz_details[0][(5 * i) + 4]
                correct = user_answers[i] == correct_answer

                question_feedback.append(
                    [questions[i], user_answers[i], correct_answer])

                if correct:
                    score += 1

            # Award achievement ID 27 - Boffin if necessary
            cur.execute(
                "SELECT * FROM CompleteAchievements "
                "WHERE (username=? AND achievement_ID=?);",
                (session["username"], 27))
            if cur.fetchone() is None:
                apply_achievement(session["username"], 27)

            # Award achievement ID 28 - Brainiac if necessary
            if score == 5:
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (session["username"], 28))
                if cur.fetchone() is None:
                    apply_achievement(session["username"], 28)

            return render_template("quiz_results.html",
                                   question_feedback=question_feedback,
                                   requestCount=get_connection_request_count(),
                                   score=score)


@application.route("/leaderboard", methods=["GET"])
def leaderboard() -> object:
    """
    Displays leaderboard of users with the most experience.

    Returns:
        The web page for viewing rankings.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM UserLevel; ")
        top_users = cur.fetchall()
        if top_users is not None:
            total_user_count = len(top_users)
            # 0 = username, 1 = XP value
            top_users.sort(key=lambda x: x[1], reverse=True)
            my_ranking = 0
            for user in top_users:
                my_ranking += 1
                if user[0] == session["username"]:
                    break
            top_users = top_users[0:min(25, len(top_users))]
            top_users = list(map(lambda x: (
                x[0], x[1], get_profile_picture(x[0]), get_level(x[0]),
                get_degree(x[0])[1]),
                                 top_users))
    session["prev-page"] = request.url
    return render_template("leaderboard.html", leaderboard=top_users,
                           requestCount=get_connection_request_count(),
                           allUsernames=get_all_usernames(),
                           myRanking=my_ranking,
                           totalUserCount=total_user_count)


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
    session["prev-page"] = request.url
    return render_template("achievements.html",
                           unlocked_achievements=unlocked_achievements,
                           locked_achievements=locked_achievements,
                           requestCount=get_connection_request_count(),
                           allUsernames=get_all_usernames(),
                           percentage=percentage,
                           percentage_color=percentage_color)


@application.route("/accept_connection_request/<username>",
                   methods=["GET", "POST"])
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
                    connection_interests = []
                    for interest in row:
                        connection_interests.append(interest[0])
                    cur.execute(
                        "SELECT hobby FROM UserHobby "
                        "WHERE username=?;",
                        (username,))
                    row = cur.fetchall()
                    connection_hobbies = []
                    for hobby in row:
                        connection_hobbies.append(hobby[0])

                    # Awards achievement ID 16 - Shared interests if necessary.
                    common_interests = set(my_interests) - (
                            set(my_interests) - set(connection_interests))
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
                    common_hobbies = set(my_hobbies) - (
                            set(my_hobbies) - set(connection_hobbies))
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

                    # Get user degree and connections degree
                    degree = get_degree(session["username"])[0]
                    degree_user2 = get_degree(username)[0]

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

                    # Gets count of other user connections who study a
                    # different degree.
                    valid_user_count2 = 0
                    for user in cons_user2:
                        cur.execute(
                            "SELECT username from UserProfile "
                            "WHERE degree!=? AND username=?;",
                            (degree_user2, user[0])
                        )
                        if cur.fetchone():
                            valid_user_count2 += 1

                    # Awards achievement ID 14 - Reaching out if necessary.
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

                    # Award achievement ID 15 - Outside your bubble if
                    # necessary
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
    """
    Blocks the given user.

    Args:
        username: The user to block.

    Returns:
        Redirection to the profile page of the user who has been blocked.
    """
    deleted = delete_connection(username)
    if deleted:
        if username != session["username"]:
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
    delete_connection(username)
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

        # Extracts blocked users.
        cur.execute(
            "SELECT Connection.user2, UserProfile.profilepicture FROM "
            "Connection LEFT JOIN UserProfile ON Connection.user2 = "
            "UserProfile.username WHERE user1=? AND connection_type=?;",
            (session["username"], "block"))
        blocked_connections = cur.fetchall()

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
                           pending=pending_connections,
                           blocked=blocked_connections)


@application.route("/admin", methods=["GET", "POST"])
def show_staff_requests() -> object:
    requests = []
    request_count = 0
    return render_template("admin.html", requests=requests,
                           requestCount=request_count)


@application.route("/terms", methods=["GET", "POST"])
def terms_page() -> object:
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
def privacy_policy_page() -> object:
    """
    Renders the privacy policy page.

    Returns:
        The web page for the privacy policy, or redirection back to T&Cs.
    """
    if request.method == "GET":
        session["prev-page"] = request.url
        return render_template("privacy_policy.html",
                               requestCount=get_connection_request_count())
    else:
        return redirect("/terms")


@application.route("/login", methods=["POST"])
def login_submit() -> object:
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
def error_test() -> object:
    """
    Redirects the user back to the login page if an error occurred.

    Returns:
        Redirection to the login page.
    """
    session["error"] = ["login"]
    return redirect("/login")


@application.route("/register", methods=["GET"])
def register_page() -> object:
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
    account = request.form.get("optradio")

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
                                         account,))
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
def post(post_id: int) -> object:
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
    # check post restrictions
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT privacy, username "
            "FROM POSTS WHERE postId=?;", (post_id,))
        row = cur.fetchone()
        if row is None:
            return render_template("error.html",
                                   message=["This post does not exist."], )
        privacy = row[0]
        username = row[1]
        # check its if its an anonymous user or a logged in user
        if session.get("username"):
            # check if the user is the same as the author of the post
            if username != session["username"]:
                # check if post is available for display
                if privacy == "private":
                    return render_template("error.html", message=[
                        "This post is private. You cannot access it."], )
                else:
                    # Checks if user trying to view the post has a connection
                    # with the post author.
                    conn_type = get_connection_type(username)
                    if conn_type is not True:
                        if privacy == "protected":
                            return render_template(
                                "error.html",
                                message=["This post is only available to "
                                         "connections."])
                    else:
                        # If the user and author are connected, check that they
                        # are close friends.
                        connection = is_close_friend(username)
                        if connection is not True:
                            if privacy == "close":
                                return render_template(
                                    "error.html", message=[
                                        "This post is only available to close "
                                        "friends."])
        else:
            if privacy != "public":
                return render_template("error.html", message=[
                    "This post is private. You cannot access it."], )

        # Gets user from database using username.
        cur.execute(
            "SELECT title, body, username, date, account_type, likes, "
            "post_type FROM POSTS WHERE postId=?;", (post_id,))
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
            (title, body, username, date_posted,
             account_type, likes, post_type) = (data[0], data[1], data[2],
                                                data[3], data[4], data[5],
                                                data[6])
            if post_type == "Image" or post_type == "Link":
                cur.execute(
                    "SELECT contentUrl "
                    "FROM PostContent WHERE postId=?;", (post_id,))
                content = cur.fetchone()
                if content is not None:
                    content = content[0]
            cur.execute(
                "SELECT *"
                "FROM Comments WHERE postId=?;", (post_id,))
            row = cur.fetchall()
            if len(row) == 0:
                session["prev-page"] = request.url
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
                    "profilePic": get_profile_picture(comment[1])
                })
            session["prev-page"] = request.url
            return render_template(
                "post_page.html", author=author, postId=post_id,
                title=title, body=body, username=username,
                date=date_posted, likes=likes, accountType=account_type,
                comments=comments, requestCount=get_connection_request_count(),
                allUsernames=get_all_usernames(),
                avatar=get_profile_picture(username), type=post_type,
                content=content)


@application.route("/fetch_posts/", methods=['GET'])
def json_posts():
    all_posts = {
        "AllPosts": []
    }
    number = request.args.get("number")
    starting_id = request.args.get("starting_id")
    content = ""    
    all_posts, content = fetch_posts(number, starting_id)
    return jsonify(all_posts)


def fetch_posts(number, starting_id):
    content = ""
    if "username" in session:
        session["prev-page"] = request.url
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()

            connections = get_all_connections(session["username"])
            connections.append((session["username"],))
            row = []
            for user in connections:
                print(user)
                cur.execute(
                    "SELECT * FROM POSTS "
                    "WHERE username=? AND postId < ?"
                    "AND privacy!='private' AND privacy!='close' LIMIT ?;", (user[0], starting_id, number))
                row += cur.fetchall()
            # Sort reverse chronologically
            row = sorted(row, key=lambda x: x[0], reverse=True)
            i = 0
            all_posts = {
                "AllPosts": []
            }
            # account type differentiation in posts db
            for user_post in row:
                if i == number:
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

                accounts = cur.fetchone()
                account_type = accounts[0]

                post_id = user_post[0]
                post_type = user_post[8]
                if post_type == "Image" or post_type == "Link":
                    cur.execute(
                        "SELECT contentUrl "
                        "FROM PostContent WHERE postId=?;", (post_id,))

                    content = cur.fetchone()
                    if content is not None:
                        content = content[0]

                cur.execute(
                    "SELECT COUNT(commentID)"
                    "FROM Comments WHERE postId=?;", (post_id,))
                comment_count = cur.fetchone()[0]

                cur.execute(
                    "SELECT likes "
                    "FROM POSTS WHERE postId=?;", (post_id,))
                like_count = cur.fetchone()[0]

                all_posts["AllPosts"].append({
                    "postId": user_post[0],
                    "title": user_post[1],
                    "profile_pic": get_profile_picture(user_post[3]),
                    "author": user_post[3],
                    "account_type": account_type,
                    "date_posted": time,
                    "body": (user_post[2])[:250] + add,
                    "post_type": user_post[8],
                    "content": content,
                    "comment_count": comment_count,
                    "like_count": like_count,
                })
                i += 1
        return all_posts, content
    else:
        return False
        


@application.route("/feed", methods=["GET"])
def feed() -> object:
    """
    Checks user is logged in before viewing their feed page.

    Returns:
        Redirection to their feed if they're logged in.
    """
    all_posts= {
        "AllPosts": []
    }
    content = ""
    session["prev-page"] = request.url
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        connections = get_all_connections(session["username"])
        connections.append((session["username"],))
        row = []
        cur.execute(
            "SELECT MAX(post_id) FROM POSTS", (user[0], starting_id, offset))
        row = cur.fetchone()

    all_posts, content, valid = fetch_posts(2,row[0])
    # Displays any error messages.
    if valid:
        if "error" in session:
            errors = session["error"]
            session.pop("error", None)
            session["prev-page"] = request.url
            return render_template("feed.html", posts=all_posts,
                                    requestCount=get_connection_request_count(),
                                    allUsernames=get_all_usernames(),
                                    errors=errors, content=content)
        else:
            session["prev-page"] = request.url
            return render_template("feed.html", posts=all_posts,
                                    requestCount=get_connection_request_count(),
                                    allUsernames=get_all_usernames(),
                                    content=content)
    else:
        return redirect("/login")


@application.route("/search_query", methods=["GET"])
def search_query():
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        chars = request.args.get("chars")
        hobby = request.args.get("hobby")
        interest = request.args.get("interest")
        name_pattern = "%" + chars + "%"
        hobby_pattern = "%" + hobby + "%"
        interest_pattern = "%" + interest + "%"

        # Filters by username, common hobbies, and interests.
        cur.execute(
            "SELECT UserProfile.username, UserHobby.hobby, "
            "UserInterests.interest FROM UserProfile "
            "LEFT JOIN UserHobby ON UserHobby.username=UserProfile.username "
            "LEFT JOIN UserInterests ON "
            "UserInterests.username=UserProfile.username "
            "WHERE (UserProfile.username LIKE ?) "
            "AND (IFNULL(hobby, '') LIKE ?) AND (IFNULL(interest, '') LIKE ?) "
            "GROUP BY UserProfile.username LIMIT 10;",
            (name_pattern, hobby_pattern, interest_pattern,))
        usernames = cur.fetchall()
        # Sorts results alphabetically.
        usernames.sort(key=lambda x: x[0])  # [(username, degree)]
        # Adds a profile picture to each user.
        usernames = list(map(lambda x: (
            x[0], x[1], x[2], get_profile_picture(x[0]), get_degree(x[0])[1]),
                             usernames))

    return jsonify(usernames)


@application.route("/submit_post", methods=["POST"])
def submit_post() -> object:
    """
    Submit post on social wall to database.

    Returns:
        Updated feed with new post added
    """
    valid = True
    form_type = request.form.get("form_type")
    post_privacy = request.form.get("privacy")
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
            fixed_height = 600
            height_percent = (fixed_height / float(im.size[1]))
            width_size = int((float(im.size[0]) * float(height_percent)))
            width_size = min(width_size, 800)
            im = im.resize((width_size, fixed_height))
            im = im.convert("RGB")
            im.save(file_path + ".jpg")
        elif file:
            valid = False

    elif form_type == "Link":
        link = request.form.get("link")
        if validate_youtube(link):
            data = urlparse(link)
            query = parse_qs(data.query)
            video_id = query["v"][0]
        else:
            valid = False

    # Only adds the post if a title has been input.
    if post_title != "" and valid is True:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            # Get account type
            cur.execute(
                "SELECT type FROM ACCOUNTS "
                "WHERE username=?;",
                (session["username"],))
            account_type = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO POSTS (title, body, username, post_type, "
                "privacy, account_type) VALUES (?, ?, ?, ?, ?, ?);",
                (
                    post_title, post_body, session["username"],
                    form_type, post_privacy, account_type))
            conn.commit()

            if form_type == "Image" and valid is True:
                cur.execute("INSERT INTO PostContent (postId, contentUrl) "
                            "VALUES (?, ?);",
                            (cur.lastrowid, application.config[
                                "UPLOAD_FOLDER"] + "//post_imgs/" +
                             file_name_hashed + ".jpg"))
                conn.commit()
            elif form_type == "Link":
                cur.execute("INSERT INTO PostContent (postId, contentUrl) "
                            "VALUES (?, ?);",
                            (cur.lastrowid, video_id))
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
def like_post() -> object:
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
            cur.execute("SELECT likes, username FROM POSTS WHERE postId=?;",
                        (post_id,))
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
        else:
            # Gets number of current likes.
            cur.execute("SELECT likes FROM POSTS WHERE postId=?;",
                        (post_id,))
            row = cur.fetchone()
            likes = row[0] - 1

            cur.execute("UPDATE POSTS SET likes=? "
                        " WHERE postId=? ;", (likes, post_id,))
            conn.commit()

            cur.execute("DELETE FROM UserLikes "
                        "WHERE (postId=? AND username=?)",
                        (post_id, session["username"]))
            conn.commit()

    return redirect("/post_page/" + post_id)


@application.route("/submit_comment", methods=["POST"])
def submit_comment() -> object:
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

            # Get username on post
            cur.execute(
                "SELECT username FROM POSTS "
                "WHERE postId=?;",
                (post_id,))
            username = cur.fetchone()[0]

            # Get number of comments
            cur.execute(
                "SELECT COUNT(commentId) FROM Comments "
                "WHERE postID=?;", (post_id,))
            row = cur.fetchone()[0]

            # Award achievement ID 21 - Hot topic if necessary
            if row >= 10:
                cur.execute(
                    "SELECT * FROM CompleteAchievements "
                    "WHERE (username=? AND achievement_ID=?);",
                    (username, 21))
                if cur.fetchone() is None:
                    apply_achievement(username, 21)

    session["postId"] = post_id
    return redirect("/post_page/" + post_id)


@application.route("/delete_post", methods=["POST"])
def delete_post() -> object:
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
    session["prev-page"] = request.url
    return render_template("error.html", message=message,
                           requestCount=get_connection_request_count(),
                           allUsernames=get_all_usernames())


@application.route("/delete_comment", methods=["POST"])
def delete_comment() -> object:
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
            session["prev-page"] = request.url
            return render_template("error.html", message=message,
                                   requestCount=get_connection_request_count(),
                                   allUsernames=get_all_usernames())
        else:
            cur.execute("DELETE FROM Comments WHERE commentId =? ",
                        (comment_id,))
            conn.commit()

    return redirect("post_page/" + post_id)


@application.route("/profile", methods=["GET"])
def user_profile() -> object:
    """
    Checks the user is logged in before viewing their profile page.

    Returns:
        Redirection to their profile if they're logged in.
    """
    if "username" in session:
        return redirect("/profile/" + session["username"])

    return redirect("/")


@application.route("/profile/<username>", methods=["GET"])
def profile(username: str) -> object:
    """
    Displays the user's profile page and fills in all of the necessary
    details. Hides the request buttons if the user is seeing their own page
    and checks if the user viewing the page has unlocked any achievements.

    Returns:
        The updated web page based on whether the details provided were valid,
        and the profile page user's privacy settings.
    """
    email = ""
    conn_type = ""
    sort_posts = []
    hobbies = []
    interests = []
    message = []

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # Gets user from database using username.
        cur.execute(
            "SELECT name, bio, gender, birthday, profilepicture, privacy FROM "
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
            name, bio, gender, birthday, profile_picture, privacy = (
                data[0], data[1], data[2], data[3], data[4], data[5])

    # If the user is logged in, specific features can then be displayed.
    if session.get("username"):

        if username == session["username"]:
            # Gets the user's posts regardless of post settings if user is the
            # owner of the profile.
            cur.execute(
                "SELECT * FROM POSTS WHERE username=?", (username,))
            sort_posts = cur.fetchall()
        else:
            # Gets the connection type between the profile owner and the user.
            cur.execute(
                "SELECT * FROM CloseFriend WHERE (user1=? AND user2=?);",
                (session["username"], username))
            if cur.fetchone() is None:
                conn_type = get_connection_type(username)
                if conn_type == "connected" and privacy == "close_friends":
                    message.append(
                        "This profile is available only to connections")
                    session["prev-page"] = request.url
                    return render_template(
                        "error.html", message=message,
                        requestCount=get_connection_request_count())
            elif conn_type == "blocked":
                message.append(
                    "Unable to view this profile since " + username +
                    " has blocked you.")
                session["prev-page"] = request.url
                return render_template(
                    "error.html", message=message,
                    requestCount=get_connection_request_count())
            else:
                conn_type = "close_friend"
                if privacy == "private":
                    message.append(
                        "This profile is only available to close friends. "
                        "Please try viewing it after logging in.")
                    session["prev-page"] = request.url
                    return render_template(
                        "error.html", message=message,
                        requestCount=get_connection_request_count())

            session["prev-page"] = request.url
            connections = get_all_connections(username)
            count = 0
            for connection in connections:
                connections[count] = connection[0]
                count += 1
            if session["username"] in connections:
                # check if user trying to view profile is a close friend
                if conn_type == "close_friend":
                    cur.execute(
                        "SELECT * "
                        "FROM POSTS WHERE username=? AND (privacy=='close' "
                        "OR privacy=='protected' OR privacy=='public')",
                        (username,))
                    sort_posts = cur.fetchall()
                elif conn_type == "connected":
                    cur.execute(
                        "SELECT * FROM POSTS WHERE username=? "
                        "AND (privacy!='private' or privacy!='close') ",
                        (username,))
                    sort_posts = cur.fetchall()
                else:
                    cur.execute(
                        "SELECT * FROM POSTS WHERE username=? "
                        "AND (privacy!='private' OR privacy!='close' OR "
                        "privacy!='protected') ",
                        (username,))
                    sort_posts = cur.fetchall()

        # Checks there are any achievements to reward
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

        # Award achievement ID 23 - Look at you if necessary
        # Set meeting to allow for secret achievement to be earned
        meeting_now = False
        if session["username"] and meeting_now:
            cur.execute(
                "SELECT * FROM CompleteAchievements "
                "WHERE (username=? AND achievement_ID=?);",
                (session["username"], 23))
            if cur.fetchone() is None:
                apply_achievement(session["username"], 23)

    else:
        # Only public posts can be viewed when not logged in
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

        time = datetime.strptime(user_post[4], "%Y-%m-%d").strftime("%d-%m-%y")
        user_posts["UserPosts"].append({
            "postId": user_post[0],
            "title": user_post[1],
            "profile_pic": "https://via.placeholder.com/600",
            "author": user_post[3],
            "account_type": user_post[6],
            "date_posted": time,
            "body": (user_post[2])[:250] + add,
            "privacy": privacy,
            "icon": icon,
            "type": user_post[8]
        })

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

    # Gets the user's email
    cur.execute("SELECT email from ACCOUNTS WHERE username=?;",
                (username,))
    row = cur.fetchall()
    if len(row) > 0:
        email = row[0][0]

    # Gets the user's six rarest achievements.
    unlocked_achievements, locked_achievements = get_achievements(username)
    first_six = unlocked_achievements[0:min(6, len(unlocked_achievements))]

    # Calculates the user's age based on their date of birth.
    datetime_object = datetime.strptime(birthday, "%Y-%m-%d")
    age = calculate_age(datetime_object)

    # get user level
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

    if session.get("username"):
        session["prev-page"] = request.url
        return render_template("profile.html", username=username,
                               name=name, bio=bio, gender=gender,
                               birthday=birthday,
                               profile_picture=profile_picture,
                               age=age, hobbies=hobbies,
                               account_type=account_type,
                               interests=interests, degree=degree,
                               email=email, posts=user_posts, type=conn_type,
                               unlocked_achievements=first_six,
                               allUsernames=get_all_usernames(),
                               requestCount=get_connection_request_count(),
                               level=level, current_xp=int(current_xp),
                               xp_next_level=int(xp_next_level),
                               progress_color=progress_color)
    else:
        session["prev-page"] = request.url
        return render_template("profile.html", username=username,
                               name=name, bio=bio, gender=gender,
                               birthday=birthday,
                               profile_picture=profile_picture,
                               age=age, hobbies=hobbies,
                               account_type=account_type,
                               interests=interests, degree=degree,
                               email=email, posts=user_posts, type="none",
                               unlocked_achievements=first_six,
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
            "SELECT birthday, bio, degree, privacy, gender FROM UserProfile "
            "WHERE username=?", (session["username"],))
        data = cur.fetchone()
        dob = data[0]
        bio = data[1]
        degree = data[2]
        privacy = data[3]
        gender = data[4]

        cur.execute(
            "SELECT hobby FROM UserHobby WHERE username=?",
            (session["username"],))
        hobbies = cur.fetchall()

        cur.execute(
            "SELECT interest FROM UserInterests WHERE username=?",
            (session["username"],))
        interests = cur.fetchall()

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
                               date=dob, bio=bio, degrees=degrees,
                               gender=gender, degree=degree,
                               privacy=privacy, hobbies=hobbies,
                               interests=interests, errors=[])

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
                             "UPLOAD_FOLDER"] + "/avatars/" + file_name_hashed
                         + ".jpg", degree, username,))
                    conn.commit()

                    # Award achievement ID 18 - Show yourself if necessary
                    cur.execute(
                        "SELECT * FROM CompleteAchievements "
                        "WHERE (username=? AND achievement_ID=?);",
                        (session["username"], 18))
                    if cur.fetchone() is None:
                        apply_achievement(username, 18)

                else:
                    cur.execute(
                        "UPDATE UserProfile SET bio=?, gender=?, birthday=?, "
                        "degree=? WHERE username=?;",
                        (bio, gender, dob, degree, username,))

                # Inserts new hobbies and interests into the database if the
                # user made a new input.

                cur.execute("DELETE FROM UserHobby WHERE "
                            "username=?;",
                            (username,))
                cur.execute("DELETE FROM UserInterests WHERE "
                            "username=?;",
                            (username,))
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
                    degree=degree, date=dob, bio=bio, privacy=privacy)


@application.route("/profile_privacy", methods=["POST"])
def profile_privacy():
    """
    Changes the privacy setting of the profile page

    Returns:
        The settings page
    """
    privacy = request.form.get("privacy")
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE UserProfile SET privacy=? WHERE username=?;",
            (privacy, session["username"],))

    return redirect("/profile")


@application.route("/logout", methods=["GET"])
def logout() -> object:
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


def calculate_age(born: datetime) -> int:
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
        conn: The connection to the database.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM UserLevel WHERE username=?;", (username,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO UserLevel (username, experience) VALUES (?, ?);",
            (username, 0))
        conn.commit()


def delete_connection(username: str) -> bool:
    """
    Deletes all connections with the given user.

    Args:
        username: The user to delete all connections with.

    Returns:
        Whether deleting connections was successful (True/False).
    """
    # Checks that the user isn't trying to remove a connection with
    # themselves.
    if username != session["username"]:
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


def get_all_connections(username: str) -> list:
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
                    return "connected"
                elif row[0] == "block":
                    return "blocked"
                return "incoming"
            else:
                return None


def get_level(username: str) -> List[int]:
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
        if row:
            return row[0]


def get_degree(username: str) -> Tuple[int, str]:
    """
    Gets the degree of a user.

    Args:
        username: The username of the user's profile picture.

    Returns:
        The degree of the user.
        The degreeID of the user.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT degree FROM UserProfile WHERE username=?;",
            (username,)
        )
        degree_id = cur.fetchone()
        if degree_id:
            cur.execute(
                "SELECT degree FROM Degree WHERE degreeId=?;",
                (degree_id[0],)
            )
            degree = cur.fetchone()
            return degree_id[0], degree[0]


def is_close_friend(username: str) -> bool:
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


def validate_quiz(quiz_name: str, questions: list) -> Tuple[bool, List[str]]:
    """
    Validates the quiz creation details which have been input by a user.

    Args:
        quiz_name: The name of the quiz input by the user.
        questions: The quiz question details input by the user.

    Returns:
        Whether the quiz is valid, and the error messages if not.
    """
    valid = True
    message = []

    # Checks that a quiz name has been made.
    if quiz_name.replace(" ", "") == "":
        valid = False
        message.append("You must enter a quiz name!")

    # Checks that all questions details have been filled in.
    for question in questions:
        for detail in question:
            if detail == "":
                valid = False
                message.append(
                    "You have not filled in details for all questions!")
                return valid, message

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


def validate_youtube(url: str):
    """
    Checks that the link is a YouTube link.

    Args:
        url: The link input by the user.

    Returns:
        Whether the link is a YouTube link (True/False).
    """
    url_regex = (
        r"(https?://)?(www\.)?"
        "(youtube|youtu|youtube-nocookie)\.(com)/"
        "(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})")
    url_regex_match = re.match(url_regex, url)

    return url_regex_match


if __name__ == "__main__":
    application.run(debug=True)
