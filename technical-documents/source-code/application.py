"""
A student network application which is presented as a web application using
the Flask module. Students each have their own profile page, and they can post
on their feed.
"""
import re
import sqlite3
from datetime import date, datetime
from string import capwords
from typing import Tuple, List

from email_validator import validate_email, EmailNotValidError
from flask import Flask, render_template, request, redirect, session
from passlib.hash import sha256_crypt

application = Flask(__name__)
application.secret_key = ("\xfd{H\xe5 <\x95\xf9\xe3\x96.5\xd1\x01O <!\xd5\""
                          "xa2\xa0\x9fR\xa1\xa8")
application.url_map.strict_slashes = False


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
    if "error" in session:
        errors = session["error"]
    session["prev-page"] = request.url
    # Clear error session variables.
    session.pop("error", None)
    return render_template("login.html", errors=errors)


@application.route("/connect/<username>", methods=["GET", "POST"])
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
        session["add"] = "You can't connect with yourself!"

    return redirect("/profile/" + username)


@application.route("/accept/<username>", methods=["GET", "POST"])
def accept(username):
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
    else:
        session["add"] = "You can't connect with yourself!"
    return redirect(session["prev-page"])


@application.route("/remove_connection/<username>")
def remove_connection(username):
    if username != session['username']:
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
                    cur.execute(
                        "DELETE FROM Connection WHERE (user1=? AND user2=?) "
                        "OR (user1=? AND user2=?);",
                        (username, session["username"], session["username"],
                         username))
                    conn.commit()
    return redirect(session["prev-page"])


@application.route("/requests", methods=["GET", "POST"])
def show_requests():
    with sqlite3.connect("database.db") as conn:
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
    return render_template("request.html", requests=requests, avatars=avatars)


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
    notifs = []
    errors = ""

    if "notifs" in session:
        notifs = session["notifs"]
    if "error" in session:
        errors = session["error"]
    session.pop("error", None)
    session.pop("notifs", None)
    session["prev-page"] = request.url

    return render_template("register.html", notifs=notifs, errors=errors)


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
            cur.execute(
                "INSERT INTO UserProfile (username, name, bio, gender, "
                "birthday, profilepicture) "
                "VALUES (?, ?, ?, ?, ?, ?);", (
                    username, fullname, "Change your bio in the settings.",
                    "Male",
                    "01/01/1970", "/static/images/default-pfp.jpg",))
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
        session["prev-page"] = request.url
        return render_template("post_page.html")
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
        session["prev-page"] = request.url
        return render_template("feed.html")
    else:
        return redirect("/login")


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
            return render_template("error.html", message=message)
        else:
            data = row[0]
            name, bio, gender, birthday, profile_picture = (
                data[0], data[1], data[2], data[3], data[4])

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

    cur.execute("SELECT email from ACCOUNTS WHERE username=?;",
                (username,))
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
            "author": "John Smith",
            "account_type": "Student",
            "time_elapsed": str(i) + " days"
        })

    # Calculates the user's age based on their date of birth.
    datetime_object = datetime.strptime(birthday, "%d/%m/%Y")
    age = calculate_age(datetime_object)
    conn_type = get_connection_type(username)
    session["prev-page"] = request.url
    print(conn_type)

    return render_template("profile.html", username=username,
                           name=name, bio=bio, gender=gender,
                           birthday=birthday, profile_picture=profile_picture,
                           age=age, hobbies=hobbies, interests=interests,
                           email=email, posts=posts, type=conn_type)


@application.route("/profile/<username>/edit", methods=["GET", "POST"])
def edit_profile(username: str) -> object:
    """
    Updates the user's profile using info from the edit profile form.

    Args:
        username: The username of the profile to edit.
    Returns:
        The updated profile page if the details provided were valid.
    """
    # Renders the edit profile form if they navigated to this page.
    if request.method == "GET":
        return render_template("settings.html")

    # Processes the form if they updated their profile using the form.
    if request.method == "POST":
        # Gets the input data from the edit profile details form.
        bio = request.form.get("bio_input")
        gender = request.form.get("gender_input")
        dob_input = request.form.get("dob_input")
        dob = datetime.strptime(dob_input, "%Y-%m-%d").date()
        profile_pic = request.form.get("profile_picture_input")
        hobbies = capwords(request.form.get("hobbies_input"))
        interests = capwords(request.form.get("interests_input"))

        # TODO: Remove print statement (used for testing).
        print(bio, gender, dob)

        # Connects to the database to perform validation.
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            # Applies changes to the user's profile details on the database if
            # valid.
            valid, message = validate_edit_profile(bio, gender, dob,
                                                   profile_pic, hobbies,
                                                   interests)
            # TODO: Remove line (used for testing).
            valid = True
            # Updates the user profile if details are valid.
            if valid is True:
                """cur.execute(
                    "UPDATE UserProfile SET bio=%s, gender=%s, birthday=%s "
                    "WHERE username=%s" %
                    (bio, gender, dob, username,),)"""
                cur.execute(
                    "UPDATE UserProfile SET bio=bio, gender=gender, "
                    "birthday=dob WHERE username=username")
                conn.commit()
                return redirect("/profile")
            # Displays error message(s) stating why their details are invalid.
            else:
                session["error"] = message
                return redirect("/profile/<username>/edit")


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
        return render_template("login.html")
    return redirect("/")


def get_connection_type(username):
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT connection_type FROM Connection WHERE user1=? "
            "AND user2=?", (session["username"], username,))
        conn.commit()
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
    Args:
        born: The user's date of birth.

    Returns:
        The age of the user in years.
    """
    today = date.today()
    return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day))


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


def validate_edit_profile(bio, gender, dob, profile_pic,
                          hobbies, interests) -> Tuple[bool, List[str]]:
    """
    Validates the details in the profile editing form.

    Args:
        bio: The bio input by the user in the form.
        gender: The gender input selected by the user in the form.
        dob: The date of birth input selected by the user in the form.
        profile_pic: The profile picture uploaded by the user in the form.
        hobbies: The hobby input by the user in the form.
        interests: The interest input by the user in the form.

    Returns:
        Whether profile editing was valid, and the error message(s) if not.
    """
    # Editing profile remains valid as long as it isn't caught by any checks.
    # If not, error messages will be provided to the user.
    valid = True
    message = []

    # Checks that the gender is male, female, or other.
    if gender not in ["Male", "Female", "Other"]:
        valid = False
        message.append("Gender must be male, female, or other!")

    # Checks that date of birth is a past date.
    if date.today() < dob:
        valid = False
        message.append("Date of birth must be a past date!")

    # Checks that the bio has a maximum of 160 characters.
    if len(bio) > 160:
        valid = False
        message.append("Bio must not exceed 160 characters!")

    # Checks that the hobby has a maximum of 24 characters.
    if len(hobbies) > 24:
        valid = False
        message.append("Hobbies must not exceed 24 characters!")

    # Checks that the interest has a maximum of 24 characters.
    if len(interests) > 24:
        valid = False
        message.append("Interests must not exceed 24 characters!")

    return valid, message


if __name__ == "__main__":
    application.run(debug=True)
