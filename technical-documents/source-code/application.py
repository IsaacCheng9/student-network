"""
A student network application which is presented as a web application using
the Flask module. Students each have their own profile page, and they can post
on their feed.
"""
import re
import sqlite3
from typing import List, Tuple

from email_validator import EmailNotValidError, validate_email
from flask import Flask, redirect, render_template, request, session
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


@application.route("/connect/<username>", methods=["GET", "POST"])
def connect_request(username):
    if session["username"] != username:
        with sqlite3.connect("database.db") as conn:
            cur.execute("SELECT * FROM Accounts WHERE username=?;", (username,))
            if cur.fetchone() is not None:
                cur = conn.cursor()
                cur.execute("SELECT * FROM Connection WHERE (user1=? AND user2=?) OR (user1=? AND user2=?);", (username,session["username"],session["username"],username))
                if cur.fetchone() is None:
                    # Gets user from database using username.
                    cur.execute("INSERT INTO Connection (user1, user2, connection_type) VALUES (?,?,?);", (session["username"], username, "request",))
                    conn.commit()
                    session["add"] = True
                else:
                    return redirect("/profile/"+username)   
            else:
                return redirect("/profilenotfound")
            return redirect("/profile/"+username)
    else:
        session["add"] = "You can't connect with yourself!"
        return redirect("/profile/"+username)
        


@application.route("/accept/<username>", methods=["GET", "POST"])




@application.route("/terms", methods=["GET"])
def terms_page():
    """
    Renders the terms and conditions page for using this application.

    Returns:
        The web page for terms and conditions.
    """
    return render_template("terms.html")


@application.route("/terms", methods=["POST"])
def terms_submit():
    """
    Navigates the user to the registration page after pressing a button.

    Returns:
        Redirection to the registration page.
    """
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
    username = request.form["username_input"]
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
def profile():
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
    hobbies = []
    interests = []

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # Gets user from database using username.
        cur.execute(
            "SELECT name, bio, gender, birthday, profilepicture FROM "
            "UserProfile WHERE username=?;", (username,))
        row = cur.fetchall()
        if row is not None:
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

    # Calculates the user's age based on their date of birth.
    datetime_object = datetime.strptime(birthday, "%d/%m/%Y")
    age = calculate_age(datetime_object)

    return render_template("/profile.html", username=username,
                            name=name, bio=bio, gender=gender,
                            birthday=birthday,
                            profile_picture=profile_picture, age=age,
                            hobbies=hobbies,
                            interests=interests)


def calculate_age(born):
    today = date.today()
    return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day))


@application.route("/logout", methods=["GET"])
def logout():
    """
    Clears the session when the user logs out.

    Returns:
        The web page for logging in.
    """
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
