"""
A student network application which is presented as a web application using
the Flask module.
"""
import re
import sqlite3
from typing import Tuple, List

from email_validator import validate_email, EmailNotValidError
from flask import Flask, render_template, request, redirect, session
from passlib.hash import sha256_crypt

application = Flask(__name__)
application.secret_key = ("\xfd{H\xe5 <\x95\xf9\xe3\x96.5\xd1\x01O <!\xd5\""
                          "xa2\xa0\x9fR\xa1\xa8")


@application.route("/", methods=["GET"])
def index_page():
    """
    Renders the feed page if logged in.

    Returns:
        The web page for user login.
    """
    if "username" in session:
        return render_template("feed.html")
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
    if "error" in session:
        errors = session["error"]
    # Clear error session variables.
    session.pop("error", None)
    return render_template("login.html", errors=errors)


@application.route("/terms", methods=["GET"])
def terms_page():
    return render_template("terms.html")


@application.route("/terms", methods=["POST"])
def terms_submit():
    return redirect("/register")


@application.route("/login", methods=["POST"])
def login_submit():
    """
    Validates the user's login details.

    Returns:
         Redirection depending on whether login was successful or not.
    """
    username = request.form["username_input"]
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
                return render_template("/feed.html")
            else:
                session["error"] = ["login"]
                return redirect("/login")
        else:
            session["error"] = ["login"]
            return redirect("/login")


@application.route("/error", methods=["GET"])
def error_test():
    session["error"] = ["login"]
    return redirect("/login")


@application.route("/register", methods=["GET"])
def register_page():
    """
    Renders the user registration page.

    Returns:
        The web page for user registration.
    """
    notifs = []
    errors = ""

    if "notifs" in session:
        notifs = session["notifs"]
    if "error" in session:
        errors = session["error"]
    session.pop("error", None)
    session.pop("notifs", None)

    return render_template("register.html", notifs=notifs, errors=errors)


# TODO: FOUND ERROR: CLICKING REGISTER BUTTON WITH NOTHING IN THE FORM
@application.route("/register", methods=["POST"])
def register_submit() -> object:
    """
    Validates the user's input submitted from the registration form.

    Returns:
        The updated web page based on whether the details provided were valid.
    """
    username = request.form["username_input"]
    password = request.form["psw_input"]
    password_confirm = request.form["psw_input_check"]
    email = request.form["email_input"]
    terms = request.form.get("terms")

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        message = []  # stores error messages to be printed to page
        valid = False
        valid, message = validate_registration(cur, username, password,
                                               password_confirm,
                                               email,terms)
        if valid is True:
            hash_password = sha256_crypt.hash(password)
            cur.execute(
                "INSERT INTO ACCOUNTS (username, password, email, type) "
                "VALUES (?, ?, ?, ?);", (username, hash_password, email,
                                         "student",))
            conn.commit()
            session["notifs"] = ["register"]
            return redirect("/register")
        else:
            session["error"] = message
            return redirect("/register")


# Checks user is logged in before viewing the post
@application.route("/postpage", methods=["GET"])
def post_page():
    if "username" in session:
        return render_template("/post_page.html")
    else:
        return redirect("/login")


# Checks user is logged in before viewing the feed page
@application.route("/feed", methods=["GET"])
def feed():
    if "username" in session:
        return render_template("/feed.html")
    else:
        return redirect("/login")


# Checks user is logged in before viewing the profile page
@application.route("/profile", methods=["GET"])
def profile():
    if "username" in session:
        return render_template("/profile.html")
    else:
        return redirect("/login")


# Clears session when the user logs out
@application.route("/logout", methods=["GET"])
def logout():
    if 'username' in session:
        session.clear()
        return render_template("/login.html")


def validate_registration(
        cur, username: str, password: str,
        password_confirm: str, email: str, terms:str) -> Tuple[bool, List[str]]:
    """
    Validates the registration details to ensure that the email address is
    valid, and that the passwords in the form match.

    Args:
        cur: Cursor for the SQLite database.
        username: The username input by the user in the form.
        password: The password input by the user in the form.
        password_confirm: The password confirmation input by the user in the
            form.
        email: The email address input by the user in the form.

    Returns:
        Whether the registration was valid, and the error message(s) if not.
    """
    # Registration remains valid as long as it isn't caught by any checks. If
    # not, error messages will be provided to the user.
    valid = True
    message = []

    # Checks that there are no null inputs.
    if (username == "" or password == "" or password_confirm == "" or
            email == ""):
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
    
    # Checks that the email address has the correct format, checks whether it
    # exists, and isn't a blacklist email.
    try:
        valid_email = validate_email(email)
        # Updates with the normalised form of the email address.
        email = valid_email.email
    # Checks if email is of valid format
    except EmailNotValidError:
        message.append("Email is invalid!")
        valid = False

    # if the format is valid check that the email address has
    # the University of Exeter domain.
    if re.search('@.*', email) is not None:
        domain = re.search('@.*', email).group()
        if domain != "@exeter.ac.uk":
            valid = False
            message.append(
                "Email address does not belong to University of Exeter!")

    # Checks that the password has a minimum length of 6 characters, and at
    # least one number.
    if len(password) <= 5 or any(char.isdigit() for char in password) is False:
        message.append("Password does not meet requirements!")
        valid = False

    # Checks that the passwords match.
    if password != password_confirm:
        message.append("Passwords do not match!")
        valid = False
    
    # Checks that the terms of service has been ticked.
    if terms is None:
        message.append("You need to accept the terms of service!")
        valid = False

    return valid, message


if __name__ == "__main__":
    application.run(debug=True)
