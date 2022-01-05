"""
Utility for changing password for all demo accounts in the database. This
changes all passwords to the password you entered using the bcrypt encryption
algorithm to ensure compatibility with the login system.
"""

import sqlite3
import bcrypt

password = input("Enter new password: ")
usernames = [
    "student1",
    "student2",
    "student3",
    "student4",
    "staffuser",
    "adminuser",
    "staffusertwo",
    "student5",
    "student6",
    "student7",
    "student8",
    "student1000",
    "student1001",
    "student1002",
]
for username in usernames:
    with sqlite3.connect("db.sqlite3") as conn:
        cur = conn.cursor()
        hash_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        cur.execute(
            "UPDATE ACCOUNTS SET password=? WHERE username=?;",
            (
                hash_password,
                username,
            ),
        )
        conn.commit()
        print("All account passwords have been successfully changed.")
