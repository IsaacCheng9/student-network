"""
A student network application which is presented as a web application using
the Flask module. Students each have their own profile page, and they can post
on their feed.
"""
import re
import sqlite3
from datetime import date, datetime
from typing import Tuple, List

from email_validator import validate_email, EmailNotValidError
from flask import Flask, render_template, request, redirect, session, json
from passlib.hash import sha256_crypt

application = Flask(__name__)
application.secret_key = ("\xfd{H\xe5 <\x95\xf9\xe3\x96.5\xd1\x01O <!\xd5\""
                          "xa2\xa0\x9fR\xa1\xa8")


@application.route("/", methods=["GET"])
def index_page():
    """
    Renders the feed page if the user is logged in.

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
    return render_template("/login.html", errors=errors)


@application.route("/terms", methods=["GET", "POST"])
def terms_page():
    if request.method == "GET":
        return render_template("terms.html")
    else:
        return redirect("/register")


@application.route("/privacy_policy", methods=["GET", "POST"])
def privacy_policy_page():
    if request.method == "GET":
        return render_template("privacy_policy.html")
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
                return render_template("/feed.html")
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
    notifs = []
    errors = ""

    if "notifs" in session:
        notifs = session["notifs"]
    if "error" in session:
        errors = session["error"]
    session.pop("error", None)
    session.pop("notifs", None)

    return render_template("register.html", notifs=notifs, errors=errors)


@application.route("/register", methods=["POST"])
def register_submit() -> object:
    """
    Validates the user's input submitted from the registration form.

    Returns:
        The updated web page based on whether the details provided were valid.
    """
    # Obtains user input from the account registration form.
    username = request.form["username_input"].lower()
    password = request.form["psw_input"]
    password_confirm = request.form["psw_input_check"]
    email = request.form["email_input"]
    terms = request.form.get("terms")

    # Connects to the database to perform validation.
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        valid, message = validate_registration(cur, username, password,
                                               password_confirm,
                                               email, terms)
        # Registers the user if the details are valid.
        if valid is True:
            hash_password = sha256_crypt.hash(password)
            cur.execute(
                "INSERT INTO Accounts (username, password, email, type) "
                "VALUES (?, ?, ?, ?);", (username, hash_password, email,
                                         "student",))
            conn.commit()
            session["notifs"] = ["register"]
            return redirect("/register")
        # Displays error message(s) stating why their details are invalid.
        else:
            session["error"] = message
            return redirect("/register")


@application.route("/post_page", methods=["GET"])
def post_page():
    """
    Checks the user is logged in before viewing their post page.

    Returns:
        The web page for their post if they're logged in.
    """
    if "username" in session:
        return render_template("/post_page.html")
    else:
        return redirect("/login")


@application.route("/feed", methods=["GET"])
def feed():
    """
    Checks user is logged in before viewing their feed page.

    Returns:
        Redirection to their feed if they're logged in.
    """
    if "username" in session:
        return render_template("/feed.html")
    else:
        return redirect("/login")


@application.route("/profile", methods=["GET"])
def user_aprofile():
    """
    Checks the user is logged in before viewing their profile page.

    Returns:
        Redirection to their profile if they're logged in.
    """
    if "username" in session:
        return redirect("/profile/"+session["username"])

    return redirect("/")

# Checks user is logged in before viewing the profile page
@application.route("/profile/<username>", methods=["GET"])
def profile(username):
    """
    Displays the user's profile page and fills in all of the necessary details.
    Also hides the request buttons if the user is seeing their own page.

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
    message = []

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # Gets user from database using username.
        cur.execute(
            "SELECT name, bio, gender, birthday, profilepicture FROM "
            "UserProfile WHERE username=?;", (username,))
        row = cur.fetchone()
        if row is None:
            message.append("The username "+username+" does not exists.")
            message.append(" Please ensure you have entered the name correctly.")
            return render_template("/error.html", message=message)
        else:
            data = row[0]
            (name, bio, gender, birthday,
                profile_picture) = data[0], data[1], data[2], data[3], data[4]

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

        cur.execute("SELECT email from ACCOUNTS WHERE username=?;", (username,))
        row = cur.fetchall()
        if len(row) > 0:
            email = row[0][0]

        # TODO: db search query in posts table for all the users posts
        # TODO: store all the users posts in a json file
        posts = {
            "UserPosts": [
            ]
        }
        for i in range(1, 10):
            posts["UserPosts"].append({
                "title": "Post " + str(i),
                "profile_pic": "https://via.placeholder.com/600",
                "author":"John Smith",
                "account_type":"Student",
                "time_elapsed": str(i) + " days"
            })

    # Calculates the user's age based on their date of birth.
    datetime_object = datetime.strptime(birthday, "%d/%m/%Y")
    age = calculate_age(datetime_object)

    return render_template("/profile.html", username=username,
                            name=name, bio=bio, gender=gender,
                            birthday=birthday,
                            profile_picture=profile_picture, age=age,
                            hobbies=hobbies,
                            interests=interests, email=email, posts=posts)


def calculate_age(born):
    today = date.today()
    return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day))


@application.route("/logout", methods=["GET"])
def logout():
    if "username" in session:
        session.clear()
        return render_template("/login.html")
    return redirect("/")


def validate_registration(
        cur, username: str, password: str, password_confirm: str,
        email: str, terms: str) -> Tuple[bool, List[str]]:
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
        terms: The terms and conditions input checkbox.

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
    if len(password) <= 7 or any(char.isdigit() for char in password) is False:
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


if __name__ == "__main__":
    application.run(debug=True)
