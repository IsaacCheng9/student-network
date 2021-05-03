from string import capwords

from flask import Blueprint
from flask import render_template, redirect
from passlib.hash import sha256_crypt

from helper import *

login_blueprint = Blueprint("login", __name__, static_folder="static",
                            template_folder="templates")


@login_blueprint.route("/", methods=["GET"])
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


@login_blueprint.route("/login", methods=["GET"])
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


@login_blueprint.route("/terms", methods=["GET", "POST"])
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


@login_blueprint.route("/privacy_policy", methods=["GET", "POST"])
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


@login_blueprint.route("/login", methods=["POST"])
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
            "SELECT password, type FROM ACCOUNTS WHERE username=?;",
            (username,))
        conn.commit()
        row = cur.fetchone()
        if row is not None:
            hashed_psw = row[0]
            account_type = row[1]
        else:
            session["error"] = ["login"]
            return redirect("/login")
        if hashed_psw is not None:
            if sha256_crypt.verify(psw, hashed_psw):
                session["username"] = username
                session["prev-page"] = request.url
                if account_type == 'admin':
                    session["admin"] = True
                    return redirect("/admin")
                else:
                    session["admin"] = False
                    return redirect("/profile")
            else:
                session["error"] = ["login"]
                return redirect("/login")
        else:
            session["error"] = ["login"]
            return redirect("/login")


@login_blueprint.route("/error", methods=["GET"])
def error_test() -> object:
    """
    Redirects the user back to the login page if an error occurred.

    Returns:
        Redirection to the login page.
    """
    session["error"] = ["login"]
    return redirect("/login")


@login_blueprint.route("/register", methods=["GET"])
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


@login_blueprint.route("/register", methods=["POST"])
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
