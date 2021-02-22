"""Handles the registration process for a new user account."""
import re
import sqlite3
from email_validator import validate_email, EmailNotValidError


def main():
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        # Gets the user inputs from the registration page.
        username = "ic324"
        password = "Password01"
        password_confirm = "Password01"
        email = "ic324@exeter.ac.uk"
        valid = validate_registration(cur, username, password,
                                      password_confirm, email)
        print(valid)
        conn.commit()


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


if __name__ == "__main__":
    main()
