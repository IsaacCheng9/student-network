"""Handles the registration process for a new user account."""


from flask.globals import request


def validate_registration():
    """
    Validates the registration details to ensure that the email address is
    valid, and that the passwords in the form match.
    """
    email = request.args.get("email")
    username = request.args.get("username")
    password = request.args.get("password")
    password_confirm = request.args.get("password_confirm")
