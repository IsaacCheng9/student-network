"""
Performs checks and actions to help the views function effectively.
"""
import os
import re
import sqlite3
import uuid
from datetime import date, datetime
from math import floor
from random import sample
from typing import Tuple, List, Sized

from PIL import Image
from email_validator import validate_email, EmailNotValidError
from flask import request, session
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def add_quiz(author, date_created, post_privacy, questions, quiz_name):
    """
    Adds quiz to the database.

    Args:
        author: Person who created the quiz.
        date_created: Date the quiz was created (YYYY/MM/DD).
        post_privacy: Privacy setting for the quiz.
        questions: Questions and answers for the quiz.
        quiz_name: Name of the quiz.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Quiz (quiz_name, date_created, author,"
            "question_1, question_1_ans_1, question_1_ans_2,"
            "question_1_ans_3, question_1_ans_4, question_2,"
            "question_2_ans_1, question_2_ans_2, question_2_ans_3,"
            "question_2_ans_4, question_3, question_3_ans_1,"
            "question_3_ans_2, question_3_ans_3, question_3_ans_4,"
            "question_4, question_4_ans_1, question_4_ans_2,"
            "question_4_ans_3, question_4_ans_4, question_5,"
            "question_5_ans_1, question_5_ans_2, question_5_ans_3,"
            "question_5_ans_4, privacy) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (
                quiz_name, date_created, author, questions[0][0],
                questions[0][1], questions[0][2], questions[0][3],
                questions[0][4], questions[1][0], questions[1][1],
                questions[1][2], questions[1][3], questions[1][4],
                questions[2][0], questions[2][1], questions[2][2],
                questions[2][3], questions[2][4], questions[3][0],
                questions[3][1], questions[3][2], questions[3][3],
                questions[3][4], questions[4][0], questions[4][1],
                questions[4][2], questions[4][3], questions[4][4],
                post_privacy))
        conn.commit()


def allowed_file(file_name) -> bool:
    """
    Checks if the file is an allowed type.

    Args:
        file_name: The name of the file uploaded by the user.

    Returns:
        Whether the file is allowed or not (True/False).
    """
    return "." in file_name and \
           file_name.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg", "gif"}


def apply_achievement(username: str, achievement_id: int):
    """
    Marks an achievement as unlocked by the user.

    Args:
        username: The user who unlocked the achievement.
        achievement_id: The ID of the achievement unlocked.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM CompleteAchievements "
            "WHERE (username=? AND achievement_ID=?);",
            (username, achievement_id))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO CompleteAchievements "
                "(username, achievement_ID, date_completed) VALUES (?, ?, ?);",
                (username, achievement_id, date.today()))
            conn.commit()
            cur.execute(
                "SELECT xp_value FROM Achievements WHERE achievement_ID=?;",
                (achievement_id,))
            exp = cur.fetchone()[0]
            check_level_exists(username, conn)
            cur.execute(
                "UPDATE UserLevel "
                "SET experience = experience + ? "
                "WHERE username=?;",
                (exp, username))
            conn.commit()

            new_notification("You have received an achievement badge!",
                             "/achievements")


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


def check_if_liked(cur, post_id: int, username: str) -> bool:
    """
    Checks if the given user has liked the post.

    Args:
        cur: Cursor for the SQLite database.
        post_id: ID of the post to check
        username: username to check if post is liked from

    Returns:
        True if post has been liked by user, False if not
    """
    cur.execute("SELECT username FROM UserLikes "
                "WHERE postId=? AND username=?;",
                (post_id, username))
    if cur.fetchone():
        return True
    return False


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
        with sqlite3.connect(DB_PATH) as conn:
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
                if row:
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
                    if row:
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


def display_short_notification_age(seconds):
    prefixes = ["y", "m", "d", "h", "m", "s"]
    values = [3600 * 24 * 365, 3600 * 31 * 24, 3600 * 24, 3600, 60, 1]

    for i in range(len(prefixes)):
        if seconds >= values[i]:
            return str(floor(seconds / values[i])) + prefixes[i]

    return "Just Now"


def fetch_posts(number: int, starting_id: int) -> Tuple[dict, str, bool]:
    """
    Fetches posts which are visible by the user logged in.

    Args:
        number: Number of posts.
        starting_id: ID of the first post to fetch, in descending order.

    Returns:
        A dictionary of details in the post, type of post, and validity of
        post.
    """
    content = ""
    all_posts = {
        "AllPosts": []
    }
    if "username" in session:
        session["prev-page"] = request.url
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()

            connections = get_all_connections(session["username"])
            connections.append((session["username"],))
            row = []
            for user in connections:
                cur.execute(
                    "SELECT * FROM POSTS "
                    "WHERE username=? AND postId <= ?"
                    "AND privacy!='private' AND privacy!='close' "
                    "ORDER BY postId DESC LIMIT ?;",
                    (user[0], starting_id, number))
                row += cur.fetchall()
            # Sort reverse chronologically
            row = sorted(row, key=lambda x: x[0], reverse=True)
            i = 0

            # account type differentiation in posts db
            for user_post in row:
                if i == int(number):
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

                cur.execute("SELECT * FROM Comments WHERE postId=? LIMIT 5;",
                            (post_id,))
                comments = cur.fetchall()

                comments = list(map(lambda x: (x[0], x[1], x[2], x[3], x[4],
                                               get_profile_picture(x[1])),
                                    comments))

                if post_type in ("Image", "Link"):
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

                liked = check_if_liked(cur, post_id, session["username"])

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
                    "liked": liked,
                    "comments": comments
                })
                i += 1
        return all_posts, content, True
    else:
        return all_posts, content, False


def get_achievements(username: str) -> Tuple[Sized, Sized]:
    """
    Gets unlocked and locked achievements for the user.

    Returns:
        A list of unlocked and locked achievements and their details.
    """
    with sqlite3.connect(DB_PATH) as conn:
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
    with sqlite3.connect(DB_PATH) as conn:
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
    with sqlite3.connect(DB_PATH) as conn:
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

    with sqlite3.connect(DB_PATH) as conn:
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
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT connection_type FROM Connection WHERE user1=? "
            "AND user2=?", (session["username"], username,))
        conn.commit()

        # Checks if there is a connection between the two users.
        row = cur.fetchone()
        if row:
            return row[0]
        else:
            cur.execute(
                "SELECT connection_type FROM Connection WHERE user1=? AND "
                "user2=?", (username, session["username"],))
            conn.commit()
            row = cur.fetchone()
            if row:
                if row[0] == "connected":
                    return "connected"
                elif row[0] == "block":
                    return "blocked"
                return "incoming"
            else:
                return None


def get_degree(username: str) -> Tuple[int, str]:
    """
    Gets the degree of a user.

    Args:
        username: The username of the user's profile picture.

    Returns:
        The degree of the user.
        The degreeID of the user.
    """
    with sqlite3.connect(DB_PATH) as conn:
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

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        check_level_exists(username, conn)
        # Get user experience
        cur.execute(
            "SELECT experience FROM "
            "UserLevel WHERE username=?;", (username,))
        row = cur.fetchone()

        exp = int(row[0])
        while exp >= xp_next_level:
            level += 1
            exp -= xp_next_level
            xp_next_level += xp_increase_per_level

        return [level, exp, xp_next_level]


def get_profile_picture(username: str) -> str:
    """
    Gets the profile picture of a user.

    Args:
        username: The username of the user's profile picture.

    Returns:
        The profile picture of the user.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT profilepicture FROM UserProfile WHERE username=?;",
            (username,)
        )
        row = cur.fetchone()
        if row:
            return row[0]


def get_quiz_details(cur, quiz_id: int) -> Tuple[list, list, str, list, str]:
    """
    Gets the details for the quiz being taken.
    Args:
        cur: Cursor for the SQLite database.
        quiz_id: The ID of the quiz being taken.

    Returns:
        Answer options, questions, and author, details, and name of the quiz.
    """
    cur.execute("SELECT * FROM Quiz WHERE quiz_id=?;", (quiz_id,))
    quiz_details = cur.fetchall()
    quiz_name = quiz_details[0][1]
    quiz_author = quiz_details[0][3]
    question_1 = quiz_details[0][4]
    question_1_options = sample(
        [quiz_details[0][5], quiz_details[0][6],
         quiz_details[0][7], quiz_details[0][8]], 4)
    question_2 = quiz_details[0][9]
    question_2_options = sample(
        [quiz_details[0][13], quiz_details[0][10],
         quiz_details[0][11], quiz_details[0][12]], 4)
    question_3 = quiz_details[0][14]
    question_3_options = sample(
        [quiz_details[0][18], quiz_details[0][15],
         quiz_details[0][16], quiz_details[0][17]], 4)
    question_4 = quiz_details[0][19]
    question_4_options = sample(
        [quiz_details[0][23], quiz_details[0][20],
         quiz_details[0][21], quiz_details[0][22]], 4)
    question_5 = quiz_details[0][24]
    question_5_options = sample(
        [quiz_details[0][28], quiz_details[0][25],
         quiz_details[0][26], quiz_details[0][27]], 4)
    # Gets a list of questions and answers to pass to the web page.
    questions = [question_1, question_2, question_3, question_4, question_5]
    answers = [question_1_options, question_2_options, question_3_options,
               question_4_options, question_5_options]
    return answers, questions, quiz_author, quiz_details, quiz_name


def get_notifications():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT body, date, url FROM notification WHERE username=? ORDER "
            "BY date DESC",
            (session["username"],))

        row = cur.fetchall()

        notification_metadata = list(
            map(lambda x: (x[0], display_short_notification_age(
                (datetime.now() - datetime.strptime(x[1],
                                                    "%Y-%m-%d "
                                                    "%H:%M:%S")).total_seconds()),
                           x[2]), row))

        return notification_metadata


def get_recommended_connections(username: str) -> list:
    """
    Gets recommended connections for a user based on mutual connections and
    degree.

    Returns:
        List of mutual connections for a user and the number of shared
        connections, as well as users with shared degree.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user2 FROM Connection "
            "WHERE user1=? AND connection_type='request' UNION ALL "
            "SELECT user1 FROM Connection "
            "WHERE user2=? AND connection_type='request'",
            (username, username))
        pending = cur.fetchall()
        recommend_type = "mutual connection"
        for count, pend in enumerate(pending):
            pending[count] = pend[0]
        connections = get_all_connections(username)
        mutual_connections = []
        for user in connections:
            user_cons = get_all_connections(user[0])
            for mutual in user_cons:
                if (mutual[0] != session["username"] and
                        mutual[0] not in pending):
                    mutual_connections = search_list(mutual_connections,
                                                     mutual, recommend_type)

        if len(mutual_connections) < 5:
            degree = get_degree(session["username"])
            if degree[0] != 1:
                cur.execute(
                    "SELECT username FROM "
                    "UserProfile WHERE degree=?;",
                    (degree[0],))
                shared_degree = cur.fetchall()
                recommend_type = "Studies " + str(degree[1])
                for user in shared_degree:
                    if len(mutual_connections) < 5:
                        if (user[0] != session["username"] and
                                user[0] not in pending):
                            mutual_connections = search_list(
                                mutual_connections,
                                user, recommend_type)
                    else:
                        break

        return mutual_connections


def is_close_friend(username: str) -> bool:
    """
    Gets whether the selected user has the logged in as a close friend.

    Returns:
        Whether the user is a close friend of the user (True/False).
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM CloseFriend WHERE (user1=? AND user2=?);",
            (session["username"], username)
        )
        if cur.fetchone():
            return True

    return False


def new_notification(body, url):
    now = datetime.now()

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO notification (username, body, date, url) VALUES (?, "
            "?, ?, ?);",
            (session["username"], body, now.strftime("%Y-%m-%d %H:%M:%S"), url)
        )

        conn.commit()


def read_socials(username: str):
    """
    Args:
        username: The username whose socials to check.

    Returns:
        The social media accounts of that user.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        socials = {}
        # Gets the user's socials
        cur.execute("SELECT social, link from UserSocial WHERE username=?;",
                    (username,))
        row = cur.fetchall()
        if len(row) > 0:
            for item in row:
                socials[item[0]] = item[1]
    return socials


def save_quiz_details() -> Tuple[date, str, str, list]:
    """
    Gets details about questions and metadata for the quiz.

    Returns:
        Author, date created, questions, and quiz name.
    """
    # Gets quiz details.
    date_created = date.today()
    author = session["username"]
    quiz_name = request.form.get("quiz_name")
    questions = [[request.form.get("question_1"),
                  request.form.get("question_1_ans_1"),
                  request.form.get("question_1_ans_2"),
                  request.form.get("question_1_ans_3"),
                  request.form.get("question_1_ans_4")],
                 [request.form.get("question_2"),
                  request.form.get("question_2_ans_1"),
                  request.form.get("question_2_ans_2"),
                  request.form.get("question_2_ans_3"),
                  request.form.get("question_2_ans_4")],
                 [request.form.get("question_3"),
                  request.form.get("question_3_ans_1"),
                  request.form.get("question_3_ans_2"),
                  request.form.get("question_3_ans_3"),
                  request.form.get("question_3_ans_4")],
                 [request.form.get("question_4"),
                  request.form.get("question_4_ans_1"),
                  request.form.get("question_4_ans_2"),
                  request.form.get("question_4_ans_3"),
                  request.form.get("question_4_ans_4")],
                 [request.form.get("question_5"),
                  request.form.get("question_5_ans_1"),
                  request.form.get("question_5_ans_2"),
                  request.form.get("question_5_ans_3"),
                  request.form.get("question_5_ans_4")]]
    return date_created, author, quiz_name, questions


def search_list(mutual_connections: list, mutual: str, recommend_type: str):
    """
    Args:
        mutual_connections: List of mutual connections with the user.
        mutual: Mutual users based on other mutual connections and degree.
        recommend_type: Reason why the user is a suggested connection.

    Returns:
        A list of mutual connections with the user.
    """
    new = True
    for count, found in enumerate(mutual_connections):
        if found[0] == mutual[0]:
            mutual_connections[count][1] += 1
            if recommend_type == "mutual connection":
                mutual_connections[count][2] = recommend_type + "s"
            new = False
            break
    if new:
        mutual_connections.append([mutual[0], 1, recommend_type])

    return mutual_connections


def update_close_connection_achievements(cur):
    """
    Updates achievements after interacting with close connections.

    Args:
        cur: Cursor for the SQLite database.
    """
    # Award achievement ID 12 - Friends if necessary
    apply_achievement(session["username"], 12)

    # Award achievement ID 13 - Friend Group if necessary
    cur.execute(
        "SELECT * FROM CloseFriend WHERE user1=?;",
        (session["username"],))
    if len(cur.fetchall()) >= 10:
        apply_achievement(session["username"], 13)


def update_comment_achievements(row: int, username: str):
    """
    Unlocks achievements for a user after making a comment.

    Args:
        row: Number of comments on the post.
        username: Author of the post.
    """
    # Award achievement ID 10 - Commentary if necessary
    apply_achievement(session["username"], 10)

    # Award achievement ID 21 - Hot topic if necessary
    if row >= 10:
        apply_achievement(username, 21)


def update_connection_achievements(cur, username: str):
    """
    Updates achievements after interacting with a connection request.

    Args:
        cur: Cursor for the SQLite database.
        username: The username of the person who requested a connection.
    """
    # Award achievement ID 4 - Connected if necessary
    apply_achievement(session["username"], 4)

    # Award achievement ID 4 to connected user
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
        apply_achievement(session["username"], 16)
        # Award achievement ID 16 to connected user
        apply_achievement(username, 16)

    # Award achievement ID 26 - Shared hobbies if necessary
    common_hobbies = set(my_hobbies) - (
            set(my_hobbies) - set(connection_hobbies))
    if common_hobbies:
        apply_achievement(session["username"], 26)
        # Award achievement ID 26 to connected user
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
        apply_achievement(session["username"], 14)
    # Award achievement ID 14 to connected user
    if valid_user_count2 >= 1:
        apply_achievement(username, 14)

    # Award achievement ID 15 - Outside your bubble if necessary
    if valid_user_count >= 10:
        apply_achievement(session["username"], 15)
    # Award achievement ID 15 to connected user
    if valid_user_count2 >= 10:
        apply_achievement(username, 15)

    # Get number of connections
    con_count_user = len(cons_user)
    # Get number of connections
    con_count_user2 = len(cons_user2)
    # Award achievement ID 5 - Popular if necessary
    if con_count_user >= 10:
        apply_achievement(session["username"], 5)
    # Award achievement ID 5 to connected user
    if con_count_user2 >= 10:
        apply_achievement(username, 5)
    # Award achievement ID 6 - Centre of Attention if necessary
    if con_count_user >= 100:
        apply_achievement(session["username"], 6)
    # Award achievement ID 6 to connected user
    if con_count_user2 >= 100:
        apply_achievement(username, 6)


def update_post_achievements(cur, likes: int, username: str):
    """
    Unlocks achievements for a user after interaction with a post.

    Args:
        cur: Cursor for the SQLite database.
        likes: Number of likes on the post.
        username: Author of the post.
    """
    # Award achievement ID 20 - First like if necessary
    apply_achievement(username, 20)

    # Award achievement ID 22 - Everyone loves you if necessary
    if likes >= 50:
        apply_achievement(username, 22)

    # Checks how many posts user has liked.
    cur.execute("SELECT COUNT(postId) FROM UserLikes"
                " WHERE username=? ;", (session["username"],))
    row = cur.fetchone()[0]
    # Award achievement ID 19 - Liking that if necessary
    if row == 1:
        apply_achievement(session["username"], 19)
    # Award achievement ID 24 - Show the love if necessary
    elif row == 50:
        apply_achievement(session["username"], 24)
    # Award achievement ID 25 - Loving everything if necessary
    elif row == 500:
        apply_achievement(session["username"], 25)


def update_profile_achievements(username: str):
    """
    Unlocks achievements for a user after interaction with a profile.

    Args:
        username: Author of the post.
    """
    # Award achievement ID 1 - Look at you if necessary
    if username == session["username"]:
        apply_achievement(session["username"], 1)

    # Award achievement ID 2 - Looking good if necessary
    if username != session["username"] and session["username"]:
        apply_achievement(session["username"], 2)

    # Award achievement ID 23 - Secret meeting
    # Set meeting to allow for secret achievement to be earned
    meeting_now = False
    special_day = (0, 0)
    today = date.today()
    if today.month == special_day[0]:
        if today.day == special_day[1]:
            meeting_now = True
    if session["username"] and meeting_now:
        apply_achievement(session["username"], 23)


def update_quiz_achievements(score: int):
    """
    Updates achievements after completing a quiz.

    Args:
        score: Number of correct answers from the quiz.
    """
    # Award achievement ID 27 - Boffin if necessary
    apply_achievement(session["username"], 27)

    # Award achievement ID 28 - Brainiac if necessary
    if score == 5:
        apply_achievement(session["username"], 28)


def upload_image(file):
    """
    Uploads the image to the website.

    Args:
        file: The file uploaded by the user.

    Returns:
        The hashed file name.
    """
    file_name_hashed = ""
    # Hashes the name of the file and resizes it.
    if allowed_file(file.filename):
        secure_filename(file.filename)
        file_name_hashed = str(uuid.uuid4())
        file_path = os.path.join(
            "./static/images" + "//post_imgs",
            file_name_hashed)

        img = Image.open(file)
        fixed_height = 600
        height_percent = (fixed_height / float(img.size[1]))
        width_size = int(
            (float(img.size[0]) * float(height_percent)))
        width_size = min(width_size, 800)
        img = img.resize((width_size, fixed_height))
        img = img.convert("RGB")
        img.save(file_path + ".jpg")
    return file_name_hashed


def update_submission_achievements(cur):
    """
    Unlocks achievements for a user after they make a submission.

    Args:
        cur: Cursor for the SQLite database.
    """
    # Award achievement ID 7 - Express yourself if necessary
    apply_achievement(session["username"], 7)

    cur.execute(
        "SELECT * FROM POSTS WHERE username=?;",
        (session["username"],))
    num_posts = cur.fetchall()
    # Award achievement ID 8 - 5 posts if necessary
    if len(num_posts) >= 5:
        apply_achievement(session["username"], 8)
    # Award achievement ID 9 - 20 posts, if necessary
    if len(num_posts) >= 20:
        apply_achievement(session["username"], 9)


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
        file: The file uploaded by the user.

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
            "./static/images" + "//avatars",
            file_name_hashed)
        img = Image.open(file)
        img = img.resize((400, 400))
        img = img.convert("RGB")
        img.save(file_path + ".jpg")
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
