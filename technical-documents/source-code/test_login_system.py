import sqlite3

import application


def test_invalid_registration():
    """Tests that invalid registration details are rejected."""
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        username = ["goodname", "goodname", "goodname", "goodname", "goodname",
                    "goodname", "goodname", "b@dname", "goodname"]
        full_name = ["Good Name", "Good Name", "Good Name", "Good Name",
                     "Good Name", "Good Name", "Bad Name_", "Good Name",
                     "Good Name"]
        password = ["goodpw123", "goodpw123", "goodpw123", "mismatch1",
                    "badpw1",
                    "badpwbad", "goodpw123", "goodpw123", "goodpw123"]
        password_confirm = ["goodpw123", "goodpw123", "goodpw123", "mismatch2",
                            "badpw1", "badpwbad", "goodpw", "goodpw123",
                            "goodpw123"]
        email = ["goodname@exeter.ac.uk", "goodname@gmail.com", "bademail@",
                 "goodname@exeter.ac.uk", "goodname@exeter.ac.uk",
                 "goodname@exeter.ac.uk", "goodname@exeter.ac.uk",
                 "goodname@exeter.ac.uk", "ic324@exeter.ac.uk"]
        terms = [None, "", "", "", "", "", "", "", ""]
        for num in range(len(username)):
            valid, message = application.validate_registration(
                cur, username[num], full_name[num], password[num],
                password_confirm[num], email[num], terms[num])
            assert valid is False


def test_valid_registration():
    """Tests that valid registration details are accepted."""
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        valid, message = application.validate_registration(
            cur, "goodname", "Good Name", "goodpw123", "goodpw123",
            "goodname@exeter.ac.uk", "")
        assert valid is True


def test_null_registration():
    """Tests that null registration details are rejected."""
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        valid, message = application.validate_registration(
            cur, "", "", "", "", "", "")
        assert valid is False
