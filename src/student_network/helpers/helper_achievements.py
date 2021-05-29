"""
Performs checks and actions to help the achievements system work effectively.
"""
import os
import sqlite3
from datetime import date
from typing import Tuple, Sized

import student_network.helpers.helper_general as helper_general
import student_network.helpers.helper_login as helper_login
import student_network.helpers.helper_profile as helper_profile
from flask import session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


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
            "SELECT * FROM CompleteAchievements "
            "WHERE (username=? AND achievement_ID=?);",
            (username, achievement_id),
        )
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO CompleteAchievements "
                "(username, achievement_ID, date_completed) VALUES (?, ?, ?);",
                (username, achievement_id, date.today()),
            )
            conn.commit()
            cur.execute(
                "SELECT xp_value FROM Achievements WHERE achievement_ID=?;",
                (achievement_id,),
            )
            exp = cur.fetchone()[0]
            helper_login.check_level_exists(username, conn)
            cur.execute(
                "UPDATE UserLevel "
                "SET experience = experience + ? "
                "WHERE username=?;",
                (exp, username),
            )
            conn.commit()

            helper_general.new_notification(
                "You have received an achievement badge!", "/achievements"
            )


def get_achievements(username: str) -> Tuple[Sized, Sized]:
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
            (username,),
        )
        unlocked_achievements = cur.fetchall()
        unlocked_achievements.sort(key=lambda x: x[3], reverse=True)

        # Get locked achievements, sorted by XP ascending.
        cur.execute(
            "SELECT description, icon, rarity, xp_value, achievement_name "
            "FROM Achievements"
        )
        all_achievements = cur.fetchall()
        locked_achievements = list(set(all_achievements) - set(unlocked_achievements))
        locked_achievements.sort(key=lambda x: x[3])

    return unlocked_achievements, locked_achievements


def update_close_connection_achievements(cur):
    """
    Updates achievements after interacting with close connections.

    Args:
        cur: Cursor for the SQLite database.
    """
    # Award achievement ID 12 - Friends if necessary
    apply_achievement(session["username"], 12)

    # Award achievement ID 13 - Friend Group if necessary
    cur.execute("SELECT * FROM CloseFriend WHERE user1=?;", (session["username"],))
    if len(cur.fetchall()) >= 10:
        apply_achievement(session["username"], 13)


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
        "SELECT interest FROM UserInterests WHERE username=?;",
        (session["username"],),
    )
    row = cur.fetchall()
    my_interests = []
    for interest in row:
        my_interests.append(interest[0])
    cur.execute("SELECT hobby FROM UserHobby WHERE username=?;", (session["username"],))
    row = cur.fetchall()
    my_hobbies = []
    for hobby in row:
        my_hobbies.append(hobby[0])
    # Get connected user interests and hobbies
    cur.execute("SELECT interest FROM UserInterests WHERE username=?;", (username,))
    row = cur.fetchall()
    connection_interests = []
    for interest in row:
        connection_interests.append(interest[0])
    cur.execute("SELECT hobby FROM UserHobby WHERE username=?;", (username,))
    row = cur.fetchall()
    connection_hobbies = []
    for hobby in row:
        connection_hobbies.append(hobby[0])
    # Awards achievement ID 16 - Shared interests if necessary.
    common_interests = set(my_interests) - (
        set(my_interests) - set(connection_interests)
    )
    if common_interests:
        apply_achievement(session["username"], 16)
        # Award achievement ID 16 to connected user
        apply_achievement(username, 16)

    # Award achievement ID 26 - Shared hobbies if necessary
    common_hobbies = set(my_hobbies) - (set(my_hobbies) - set(connection_hobbies))
    if common_hobbies:
        apply_achievement(session["username"], 26)
        # Award achievement ID 26 to connected user
        apply_achievement(username, 26)

    # Get connections
    cons_user = helper_general.get_all_connections(session["username"])
    cons_user2 = helper_general.get_all_connections(username)
    # Get user degree and connections degree
    degree = helper_profile.get_degree(session["username"])[0]
    degree_user2 = helper_profile.get_degree(username)[0]
    # Get count of connections who study a different degree
    valid_user_count = 0
    for user in cons_user:
        cur.execute(
            "SELECT username from UserProfile WHERE degree!=? AND username=?;",
            (degree, user[0]),
        )
        if cur.fetchone():
            valid_user_count += 1
    # Gets count of other user connections who study a
    # different degree.
    valid_user_count2 = 0
    for user in cons_user2:
        cur.execute(
            "SELECT username from UserProfile WHERE degree!=? AND username=?;",
            (degree_user2, user[0]),
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
    cur.execute(
        "SELECT COUNT(postId) FROM UserLikes WHERE username=? ;",
        (session["username"],),
    )
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
    special_day = (5, 27)
    today = date.today()
    if today.month == special_day[0] and today.day == special_day[1]:
        meeting_now = True
    if session["username"] and meeting_now:
        apply_achievement(session["username"], 23)


def update_quiz_achievements(score: int, other_user: bool=False):
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

    # Award achievement ID 30 - Trivia writer if necessary
    if other_user:
        apply_achievement(session["username"], 30)
   
def update_flashcard_achievements(author, plays):
    """
    Updates achievements after playing a flashcard set.

    Args:
        author: Author of the set being viewed
    """
    # Award achievement ID 32 - Learning if necessary
    apply_achievement(session["username"], 31)

    # Award achievement ID 32 - Teacher if necessary
    if session["username"] != author:
        apply_achievement(author, 32)
    
    # Award achievement ID 32 - Professor if necessary
    if plays == 50:
        apply_achievement(author, 33)
