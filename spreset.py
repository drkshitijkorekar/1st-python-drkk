import sqlite3

conn = sqlite3.connect('spider.sqlite')
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS Pages')
cur.execute('DROP TABLE IF EXISTS Links')
conn.commit()
conn.close()

print("Database reset complete.")