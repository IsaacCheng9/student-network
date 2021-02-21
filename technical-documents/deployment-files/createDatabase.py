import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute("CREATE TABLE COMMENTS ([username] text, [comment] text)")

conn.commit()