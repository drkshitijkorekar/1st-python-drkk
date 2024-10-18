import sqlite3

conn = sqlite3.connect('spider.sqlite')
cur = conn.cursor()

# Fetch the pages with ranks and print them
cur.execute('SELECT url, new_rank FROM Pages ORDER BY new_rank DESC LIMIT 100')
for row in cur:
    print(f"URL: {row[0]}, Rank: {row[1]}")

cur.close()