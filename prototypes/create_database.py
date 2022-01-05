import sqlite3

conn = sqlite3.connect("../db.sqlite3")
c = conn.cursor()

c.execute(
    "CREATE TABLE Accounts([username] text, [password] text, "
    "[email] text, [type] text)"
)

conn.commit()
