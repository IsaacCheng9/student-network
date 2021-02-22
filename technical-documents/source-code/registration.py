"""Handles the registration process for a new user account."""

import sqlite3
from flask.globals import request
from email_validator import validate_email, EmailNotValidError


def main():
    with sqlite3.connect("database.db") as con:
        c = con.cursor()
        valid = validate_registration(c)
        print(valid)
        con.commit()


def validate_registration(c) -> bool:
    """
    Validates the registration details to ensure that the email address is
    valid, and that the passwords in the form match.

    Returns:
        valid (bool): States whether the registration details are valid.
    """
    # Gets the user inputs from the registration page.
    # TODO: Connect function to Flask web application and test if it works.
    """
    email = request.args.get("email_input")
    username = request.args.get("username_input")
    password = request.args.get("psw_input")
    password_confirm = request.args.get("psw_input_check")

    c.execute("INSERT INTO Accounts VALUES ('test123', 'Password01', "
              "'test123@exeter.ac.uk', 'student');")
    """
    email = "ic324@exeter.ac.uk"
    username = "test123"
    password = "Password01"
    password_confirm = "Password01"

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

    # Checks that the username hasn't already been registered.
    # TODO: Fix return of query not being checked properly.
    """
    c.execute("SELECT COUNT(username) FROM Accounts WHERE username='test123';")
    print(c.fetchone())
    if c.fetchone() != "(0,)":
        valid = False
    """

    # Checks that the password has a minimum length of 6 characters, and at
    # least one number.
    if len(password) <= 5 or any(char.isdigit() for char in password) is False:
        valid = False

    # Checks that the passwords match.
    if password != password_confirm:
        valid = False

    return valid


if __name__ == "__main__":
    main()
