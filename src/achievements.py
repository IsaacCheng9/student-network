from flask import Blueprint, render_template

from helper import *

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
    unlocked_achievements, locked_achievements = get_achievements(
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
    apply_achievement(session["username"], 3)

    session["prev-page"] = request.url
    return render_template("achievements.html",
                           unlocked_achievements=unlocked_achievements,
                           locked_achievements=locked_achievements,
                           requestCount=get_connection_request_count(),
                           allUsernames=get_all_usernames(),
                           percentage=percentage,
                           percentage_color=percentage_color)
