import sqlite3

import application


def test_validate_registration():
    """Tests that registration validation is correct."""
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        username = "johndoe"
        full_name = "John Doe"
        password = "SecurePassword123"
        password_confirm = "SecurePassword123"
        email = "johndoe@exeter.ac.uk"
        terms = None
        valid, message = application.validate_registration(
            cur, username, full_name, password, password_confirm, email,
            terms)
        assert valid is False
