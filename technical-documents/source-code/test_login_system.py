import sqlite3

import application


def test_validate_registration():
    """Tests that registration validation is performed correctly."""
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        # Tests invalid details.
        username = ["goodname", "goodname", "goodname", "goodname", "goodname",
                    "goodname", "goodname", "b@dname"]
        full_name = ["Good Name", "Good Name", "Good Name", "Good Name",
                     "Good Name", "Good Name", "Bad Name_", "Good Name"]
        password = ["goodpw123", "goodpw123", "goodpw123", "mismatch1",
                    "badpw1",
                    "badpwbad", "goodpw123", "goodpw123"]
        password_confirm = ["goodpw123", "goodpw123", "goodpw123", "mismatch2",
                            "badpw1", "badpwbad", "goodpw", "goodpw123"]
        email = ["goodname@exeter.ac.uk", "goodname@gmail.com", "bademail@",
                 "goodname@exeter.ac.uk", "goodname@exeter.ac.uk",
                 "goodname@exeter.ac.uk", "goodname@exeter.ac.uk",
                 "goodname@exeter.ac.uk"]
        terms = [None, "", "", "", "", "", "", ""]
        for num in range(len(username)):
            valid, message = application.validate_registration(
                cur, username[num], full_name[num], password[num],
                password_confirm[num], email[num], terms[num])
            assert valid is False

        # Tests valid details.
        valid, message = application.validate_registration(
            cur, "goodname", "Good Name", "goodpw123", "goodpw123",
            "goodname@exeter.ac.uk", "")
        assert valid is True

        # Tests null details.
        valid, message = application.validate_registration(
            cur, "", "", "", "", "", "")
        assert valid is False
