"""
Handles the view for staff administration tools and related functionality.
"""
from flask import Blueprint, render_template, redirect

from student_network.helper import *

staff_blueprint = Blueprint("staff", __name__, static_folder="static",
                            template_folder="templates")


@staff_blueprint.route("/admin", methods=["GET", "POST"])
def show_staff_requests() -> object:
    """
    Displays requests to sign up as a staff member.

    Returns:
        The web page for handling administration.
    """
    if "admin" in session:
        if not session["admin"]:
            return render_template("error.html", message=[
                "You are not logged in to an admin account"],
                                   requestCount=get_connection_request_count())
        with sqlite3.connect("database.db") as conn:
            # Loads the list of connection requests and their avatars.
            requests = []
            cur = conn.cursor()
            # Extracts incoming requests.
            cur.execute("SELECT username FROM ACCOUNTS "
                        "WHERE type='pending_staff';")
            conn.commit()
            row = cur.fetchall()
            request_count = get_connection_request_count()
            if len(row) > 0:
                for elem in row:
                    requests.append(elem[0])

            return render_template("admin.html", requests=requests,
                                   requestCount=request_count)
    else:
        return render_template("error.html", message=[
            "You are not logged in to an admin account"],
                               requestCount=get_connection_request_count())


@staff_blueprint.route("/accept_staff/<username>", methods=["GET", "POST"])
def accept_staff(username: str):
    """
    Accepts user as a staff member.

    Args:
        username: The user to accept as a staff member.

    Returns:
        Redirection to the administration page.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("UPDATE ACCOUNTS SET type=? "
                    " WHERE username=? ;", ("staff", username))
    return redirect("/admin")


@staff_blueprint.route("/reject_staff/<username>", methods=["GET", "POST"])
def reject_staff(username: str):
    """
    Rejects user as staff member.

    Args:
        username: The user to reject as a staff member.

    Returns:
        Redirection to the administration page.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("UPDATE ACCOUNTS SET type=? "
                    " WHERE username=? ;", ("student", username))
    return redirect("/admin")
