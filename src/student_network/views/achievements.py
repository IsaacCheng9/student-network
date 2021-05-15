"""
Handles the view for achievements and related functionality.
"""

import sqlite3

import student_network.helpers.helper_achievements as helper_achievements
import student_network.helpers.helper_connections as helper_connections
import student_network.helpers.helper_general as helper_general
from flask import Blueprint, render_template
from flask import request, session

achievements_blueprint = Blueprint("achievements", __name__,
                                   static_folder="static",
                                   template_folder="templates")


@achievements_blueprint.route("/achievements", methods=["GET"])
def achievements() -> object:
    """
    Display achievements which the user has unlocked/locked.

    Returns:
        The web page for viewing achievements.
    """
    unlocked_achievements, locked_achievements = \
        helper_achievements.get_achievements(
            session["username"])

    # Displays the percentage of achievements unlocked.
    percentage = int(100 * len(unlocked_achievements) /
                     (len(unlocked_achievements) + len(locked_achievements)))
    percentage_color = "green"
    if percentage < 75:
        percentage_color = "yellow"
    if percentage < 50:
        percentage_color = "orange"
    if percentage < 25:
        percentage_color = "red"

    # Award achievement ID 3 - Show it off if necessary
    helper_achievements.apply_achievement(session["username"], 3)

    session["prev-page"] = request.url
    return render_template("achievements.html",
                           unlocked_achievements=unlocked_achievements,
                           locked_achievements=locked_achievements,
                           requestCount=
                           helper_connections.get_connection_request_count(),
                           allUsernames=helper_general.get_all_usernames(),
                           percentage=percentage,
                           percentage_color=percentage_color,
                           notifications=helper_general.get_notifications())


@achievements_blueprint.route("/leaderboard", methods=["GET"])
def leaderboard() -> object:
    """
    Displays leaderboard of users with the most experience.

    Returns:
        The web page for viewing rankings.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM UserLevel")
        top_users = cur.fetchall()
        if top_users:
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
                x[0], x[1],
                student_network.helpers.helper_profile.get_profile_picture(
                    x[0]),
                student_network.helpers.helper_profile.get_level(x[0]),
                student_network.helpers.helper_profile.get_degree(x[0])[1]),
                                 top_users))
    session["prev-page"] = request.url
    return render_template("leaderboard.html", leaderboard=top_users,
                           requestCount=
                           helper_connections.get_connection_request_count(),
                           allUsernames=helper_general.get_all_usernames(),
                           myRanking=my_ranking,
                           totalUserCount=total_user_count,
                           notifications=helper_general.get_notifications())
