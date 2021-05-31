"""
Performs checks and actions to help the general system work effectively.
"""
import os
import sqlite3
from datetime import datetime
from math import floor

from flask import session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def allowed_file(file_name) -> bool:
    """
    Checks if the file is an allowed type.

    Args:
        file_name: The name of the file uploaded by the user.

    Returns:
        Whether the file is allowed or not (True/False).
    """
    return "." in file_name and file_name.rsplit(".", 1)[1].lower() in {
        "png",
        "jpg",
        "jpeg",
        "gif",
    }


def display_short_notification_age(seconds):
    prefixes = ["y", "mo", "d", "h", "m", "s"]
    values = [3600 * 24 * 365, 3600 * 31 * 24, 3600 * 24, 3600, 60, 1]

    for i in range(len(prefixes)):
        if seconds >= values[i]:
            return str(floor(seconds / values[i])) + prefixes[i]

    return "Just Now"


def get_all_connections(username: str) -> list:
    """
    Gets a list of all usernames that are connected to the logged in user.

    Returns:
        A list of all usernames that are connected to the logged in user.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user2 FROM Connection "
            "WHERE user1=? AND connection_type='connected' UNION ALL "
            "SELECT user1 FROM Connection "
            "WHERE user2=? AND connection_type='connected'",
            (username, username),
        )
        connections = cur.fetchall()

        return connections


def get_all_usernames() -> list:
    """
    Gets a list of all usernames that are registered.

    Returns:
        A list of all usernames that have been registered.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT username FROM Accounts")

        row = cur.fetchall()

        return row


def get_notifications():
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT body, date, url FROM notification WHERE username=? ORDER "
            "BY date DESC",
            (session["username"],),
        )

        row = cur.fetchall()

        notification_metadata = list(
            map(
                lambda x: (
                    x[0],
                    display_short_notification_age(
                        (
                            datetime.now()
                            - datetime.strptime(x[1], "%Y-%m-%d " "%H:%M:%S")
                        ).total_seconds()
                    ),
                    x[2],
                ),
                row,
            )
        )

        return notification_metadata


def check_level_exists(username: str, conn):
    """
    Checks that a user has a record in the database for their level.

    Args:
        username: The username of the user to check.
        conn: The connection to the database.
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM UserLevel WHERE username=?;", (username,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO UserLevel (username, experience) VALUES (?, ?);", (username, 0)
        )
        conn.commit()


def one_exp(cur, username: str):
    """
    Awards 1 exp point

    Args:
        username: user to award exp to
    """
    cur.execute(
        "UPDATE UserLevel SET experience = experience + 1 WHERE username=?;",
        (username,),
    )


def get_exp(username: str):
    """
    Get current exp of given user

    Args:
        username: user to find exp value of

    Returns:
        exp of user
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        check_level_exists(username, conn)
        # Get user experience
        cur.execute("SELECT experience FROM UserLevel WHERE username=?;", (username,))
        row = cur.fetchone()

        return int(row[0])


def new_notification(body, url):
    now = datetime.now()

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO notification (username, body, date, url) VALUES (?, "
            "?, ?, ?);",
            (session["username"], body, now.strftime("%Y-%m-%d %H:%M:%S"), url),
        )

        conn.commit()


def new_notification_username(username, body, url):
    now = datetime.now()

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO notification (username, body, date, url) VALUES (?, "
            "?, ?, ?);",
            (username, body, now.strftime("%Y-%m-%d %H:%M:%S"), url),
        )

        conn.commit()
