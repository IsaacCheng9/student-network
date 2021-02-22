import re
from flask import Flask, render_template, request, redirect, session
from email_validator import validate_email, EmailNotValidError
from passlib.hash import sha256_crypt
import sqlite3

application = Flask(__name__)
application.secret_key = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'


@application.route('/', methods=['GET'])
def index_page():
    return redirect("/login")


@application.route('/login', methods=['GET'])
def login_page():
    errors = []
    if 'error' in session:
        errors = session['error']
    session.pop('error', None)
    return render_template('login.html', errors=errors)


@application.route('/login', methods=['POST'])
def login_submit():
    username = request.form['username_input']
    psw = request.form['psw_input']
    # Get user from database using username
    # Compare password with hashed password
    # Compare using sha256_crypt.verify(psw, hashed_password)
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT password FROM Accounts WHERE username=?;", (username,))
        hashed_psw = cur.fetchone()[0]
        conn.commit()
        if hashed_psw is not None:
            if(sha256_crypt.verify(psw, hashed_psw)):
                return redirect("/postpage")
            else:
                session['error'] = ['login']
                return redirect("/login")
        else:
            session['error'] = ['login']
            return redirect("/login")


@application.route('/error', methods=['GET'])
def errortest():
    session['error'] = ['login']
    return redirect("/login")


@application.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')


@application.route('/register', methods=['POST'])
def register_submit():
    username = request.form["username_input"]
    password = request.form["psw_input"]
    password_confirm = request.form["psw_input_check"]
    email = request.form["email_input"]
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        if validate_registration(cur, username, password, password_confirm,
                                 email) is True:
            hash_password = sha256_crypt.hash(password)
            cur.execute("INSERT INTO ACCOUNTS (username, password, email, type) VALUES (?, ?, ?, ?);",
                        (username, hash_password, email, 'student',))
            conn.commit()
            return redirect("/postpage")
        else:
            print("Registration validation failed.")
            session['error'] = ['passwordMatch']
            return redirect("/register")


@application.route('/postpage', methods=['GET'])
def post_page():
    return render_template('postpage.html')


def validate_registration(cur, username: str, password: str,
                          password_confirm: str, email: str) -> bool:
    """
    Validates the registration details to ensure that the email address is
    valid, and that the passwords in the form match.

    Arguments:
        cur: Cursor for the SQLite database.
        username: The username input by the user in the form.
        password: The password input by the user in the form.
        password_confirm: The password confirmation input by the user in the
            form.
        email: The email address input by the user in the form.

    Returns:
        valid (bool): States whether the registration details are valid.
    """
    valid = True

    # Checks that the email address has the correct format, checks whether it
    # exists, and isn't a blacklist email.
    try:
        valid_email = validate_email(email)
        # Updates with the normalised form of the email address.
        email = valid_email.email
    except EmailNotValidError:
        print("Email is invalid!")
        valid = False

    # Checks that the email address has the University of Exeter domain.
    domain = re.search('@.*', email).group()
    if domain != "@exeter.ac.uk":
        print("Email address does not belong to University of Exeter!")
        valid = False

    # Checks that the username hasn't already been registered.
    cur.execute("SELECT * FROM Accounts WHERE username=?;", (username,))
    if cur.fetchone() is not None:
        print("Username has already been registered!")
        valid = False

    # Checks that the password has a minimum length of 6 characters, and at
    # least one number.
    if len(password) <= 5 or any(char.isdigit() for char in password) is False:
        print("Password does not meet requirements!")
        valid = False

    # Checks that the passwords match.
    if password != password_confirm:
        print("Passwords do not match!")
        valid = False

    return valid


if __name__ == '__main__':
    application.run(debug=True)


#print("password1 -> " + password)
#print("password2 -> " + password2)

#print(sha256_crypt.verify("myPassword123", password))
#print(sha256_crypt.verify("myPassword1234", password))
