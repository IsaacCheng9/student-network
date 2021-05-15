"""
Performs checks and actions to help the login system work effectively.
"""
import re
from typing import Tuple, List

from email_validator import validate_email, EmailNotValidError


def check_level_exists(username: str, conn):
    """
    Checks that a user has a record in the database for their level.

    Args:
        username: The username of the user to check.
        conn: The connection to the database.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM UserLevel WHERE username=?;", (username,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO UserLevel (username, experience) VALUES (?, ?);",
            (username, 0))
        conn.commit()


def validate_registration(
        cur, username: str, full_name: str, password: str,
        password_confirm: str,
        email: str, terms: str) -> Tuple[bool, List[str]]:
    """
    Validates the registration details to ensure that the email address is
    valid, and that the passwords in the form match.

    Args:
        cur: Cursor for the SQLite database.
        username: The username input by the user in the form.
        full_name: The full name input by the user in the form.
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
    if (username == "" or full_name == "" or password == "" or
            password_confirm == "" or email == ""):
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

    # Checks that the full name doesn't exceed 40 characters.
    if len(full_name) > 40:
        message.append("Full name exceeds 40 characters!")
        valid = False
    # Checks that the full name only contains valid characters.
    if not all(x.isalpha() or x.isspace() for x in full_name):
        message.append("Full name must only contain letters and spaces!")
        valid = False

    # Checks that the email hasn't already been registered.
    cur.execute("SELECT * FROM Accounts WHERE email=?;", (email,))
    if cur.fetchone() is not None:
        message.append("Email has already been registered!")
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

    # Checks that the password has a minimum length of 8 characters, and at
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
