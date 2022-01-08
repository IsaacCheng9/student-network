import sqlite3

import student_network.helpers.helper_login as helper_login
from pytest_steps import test_steps


@test_steps(
    "terms_not_accepted",
    "not_university_email",
    "not_valid_email",
    "password_mismatch",
    "password_no_number",
    "username_too_short",
    "full_name_contains_symbol",
    "username_contains_symbol",
)
def test_invalid_registration():
    """
    Tests that invalid registration details are rejected.
    """
    with sqlite3.connect("db.sqlite3") as conn:
        cur = conn.cursor()

        # Invalid registration as terms haven't been accepted.
        username = "goodname"
        full_name = "Good Name"
        password = "goodpw123"
        password_confirm = "goodpw123"
        email = "goodname@exeter.ac.uk"
        terms = None
        valid, _ = helper_login.validate_registration(
            cur,
            username,
            full_name,
            password,
            password_confirm,
            email,
            terms,
        )
        assert valid is False
        yield

        # Invalid registration as the email address isn't from a university.
        email = "goodnamebademail@gmail.com"
        terms = ""
        valid, _ = helper_login.validate_registration(
            cur,
            username,
            full_name,
            password,
            password_confirm,
            email,
            terms,
        )
        assert valid is False
        yield

        # Invalid registration as the email address has an invalid format.
        email = "bademail@"
        valid, _ = helper_login.validate_registration(
            cur,
            username,
            full_name,
            password,
            password_confirm,
            email,
            terms,
        )
        assert valid is False
        yield

        # Invalid registration as the passwords don't match.
        password_confirm = "mismatch"
        email = "goodname@exeter.ac.uk"
        valid, _ = helper_login.validate_registration(
            cur,
            username,
            full_name,
            password,
            password_confirm,
            email,
            terms,
        )
        assert valid is False
        yield

        # Invalid registration as the password doesn't contain a number.
        password = "badpassword"
        password_confirm = "badpassword"
        email = "goodname@exeter.ac.uk"
        valid, _ = helper_login.validate_registration(
            cur,
            username,
            full_name,
            password,
            password_confirm,
            email,
            terms,
        )
        assert valid is False
        yield

        # Invalid registration as the password doesn't contain eight
        # characters.
        password = "badpw1"
        password_confirm = "badpw1"
        email = "goodname@exeter.ac.uk"
        valid, _ = helper_login.validate_registration(
            cur,
            username,
            full_name,
            password,
            password_confirm,
            email,
            terms,
        )
        assert valid is False
        yield

        # Invalid registration as the full name contains a symbol.
        full_name = "Bad Name_"
        password = "goodpw123"
        password_confirm = "goodpw123"
        email = "goodname@exeter.ac.uk"
        valid, _ = helper_login.validate_registration(
            cur,
            username,
            full_name,
            password,
            password_confirm,
            email,
            terms,
        )
        assert valid is False
        yield

        # Invalid registration as the username contains a symbol.
        username = "b@dname"
        full_name = "Good Name"
        password = "goodpw123"
        password_confirm = "goodpw123"
        email = "goodname@exeter.ac.uk"
        valid, _ = helper_login.validate_registration(
            cur,
            username,
            full_name,
            password,
            password_confirm,
            email,
            terms,
        )
        assert valid is False
        yield


def test_valid_registration():
    """
    Tests that valid registration details are accepted.
    """
    with sqlite3.connect("db.sqlite3") as conn:
        cur = conn.cursor()
        valid, _ = helper_login.validate_registration(
            cur,
            "goodname",
            "Good Name",
            "goodpw123",
            "goodpw123",
            "goodname@exeter.ac.uk",
            "",
        )
        assert valid is True


def test_null_registration():
    """
    Tests that null registration details are rejected.
    """
    with sqlite3.connect("db.sqlite3") as conn:
        cur = conn.cursor()
        valid, _ = helper_login.validate_registration(cur, "", "", "", "", "", "")
        assert valid is False


# TODO: Fix this test.
# def test_login_route():
#     app = helper_login.helper_login
#     client = app.test_client()
#     url = "/login"

#     response = client.get(url)
#     assert response.status_code == 200

# TODO: Fix this test.
# def test_register_route():
#     app = helper_login.helper_login
#     client = app.test_client()
#     url = "/register"

#     response = client.get(url)
#     assert response.status_code == 200
