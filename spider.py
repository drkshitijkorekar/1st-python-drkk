import sqlite3
import urllib.parse
import ssl
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Connect to SQLite database (create one if it doesn't exist)
conn = sqlite3.connect('spider.sqlite')
cur = conn.cursor()

# Create tables to store pages and links
cur.execute('''
CREATE TABLE IF NOT EXISTS Pages (
    id INTEGER PRIMARY KEY, url TEXT UNIQUE, html TEXT, error INTEGER, old_rank REAL, new_rank REAL)
''')
cur.execute('''
CREATE TABLE IF NOT EXISTS Links (
    from_id INTEGER, to_id INTEGER)
''')

# Retrieve the starting URL or get it from the database if already present
cur.execute('SELECT id,url FROM Pages WHERE html IS NULL AND error IS NULL ORDER BY RANDOM() LIMIT 1')
row = cur.fetchone()
if row is None:
    start_url = input('Enter web URL (default is https://umich.edu): ')
    if len(start_url) < 1: 
        start_url = 'https://umich.edu'
    # Insert the starting URL into the Pages table
    cur.execute('INSERT OR IGNORE INTO Pages (url, html, new_rank) VALUES (?, NULL, 1.0)', (start_url,))
    conn.commit()
else:
    print("Restarting from", row[1])

num_pages = 0
while num_pages < 100:  # Crawl approximately 100 pages
    cur.execute('SELECT id,url FROM Pages WHERE html IS NULL AND error IS NULL ORDER BY RANDOM() LIMIT 1')
    row = cur.fetchone()
    if row is None:
        print("No more unretrieved pages found")
        break

    from_id = row[0]
    url = row[1]
    print(f"Retrieving: {url}")

    # Create a request object with a User-Agent header
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    # Attempt to retrieve the page
    try:
        document = urlopen(req, context=ctx).read()
        html = document.decode()
        if len(html) < 1:
            cur.execute('UPDATE Pages SET error=1 WHERE url=?', (url,))
            conn.commit()
            continue
    except Exception as e:
        cur.execute('UPDATE Pages SET error=1 WHERE url=?', (url,))
        conn.commit()
        print(f"Failed to retrieve or parse page: {e}")
        continue

    # Store the retrieved HTML in the database
    cur.execute('UPDATE Pages SET html=? WHERE url=?', (html, url))
    conn.commit()

    # Parse the retrieved HTML using BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    links = soup('a')

    # Insert links into the Links table
    for tag in links:
        href = tag.get('href', None)
        if href is None: 
            continue

        # Resolve relative URLs
        full_url = urllib.parse.urljoin(url, href)

        # Ignore URLs that are not HTTP/HTTPS
        if not full_url.startswith('http'):
            continue

        # Avoid spidering URLs pointing to file types
        if full_url.endswith(('.pdf', '.jpg', '.png', '.docx', '.xlsx')):
            continue

        # Insert the found URL into the Pages table (if not already present)
        cur.execute('INSERT OR IGNORE INTO Pages (url, html, new_rank) VALUES (?, NULL, 1.0)', (full_url,))
        conn.commit()

        # Get the ID of the newly inserted page
        cur.execute('SELECT id FROM Pages WHERE url=? LIMIT 1', (full_url,))
        to_id = cur.fetchone()[0]

        # Insert the link between the current page (from_id) and the linked page (to_id)
        cur.execute('INSERT OR IGNORE INTO Links (from_id, to_id) VALUES (?, ?)', (from_id, to_id))

    num_pages += 1
    conn.commit()

cur.close()
print(f"Spidering complete. Crawled {num_pages} pages.")