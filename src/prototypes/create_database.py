import sqlite3

conn = sqlite3.connect('../database.db')
c = conn.cursor()

c.execute("CREATE TABLE Accounts([username] text, [password] text, "
          "[email] text, [type] text)")

conn.commit()
