import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('spider.sqlite')
cur = conn.cursor()

print("Creating JSON output in spider.js...")
howmany = int(input("How many nodes? "))

# Fetch the required data
cur.execute('''SELECT COUNT(from_id) AS inbound, old_rank, new_rank, Pages.id, url 
               FROM Pages JOIN Links ON Pages.id = Links.to_id
               WHERE html IS NOT NULL AND ERROR IS NULL
               GROUP BY Pages.id ORDER BY Pages.id, inbound''')

# Create a JSON output file
with open('spider.js', 'w') as fhand:
    nodes = []
    maxrank = None
    minrank = None
    url_count = 0  # Counter for the number of pages crawled
    starting_url = ''  # Variable for the starting URL

    for row in cur:
        if url_count == 0:  # Save the starting URL
            starting_url = row[4]
        nodes.append(row)
        rank = row[2]
        if maxrank is None or maxrank < rank: maxrank = rank
        if minrank is None or minrank > rank: minrank = rank
        url_count += 1  # Increment page count
        if url_count >= howmany: break  # Stop if we've reached the specified number of nodes

    if maxrank == minrank or maxrank is None or minrank is None:
        print("Error - please run sprank.py to compute page rank")
        quit()

    fhand.write('spiderJson = {"starting_url": "' + starting_url + '", "url_count": ' + str(url_count) + ', "nodes":[\n')
    count = 0
    node_map = {}

    for row in nodes:
        if count > 0: 
            fhand.write(',\n')
        rank = row[2]
        normalized_rank = 19 * ((rank - minrank) / (maxrank - minrank))  # Normalize rank
        fhand.write('{"weight":'+str(row[0])+',"rank":'+str(normalized_rank)+',')
        fhand.write('"id":'+str(row[3]) + ', "url":"' + row[4] + '"}')
        node_map[row[3]] = count
        count += 1
    fhand.write('],\n')

    # Write links
    cur.execute('''SELECT DISTINCT from_id, to_id FROM Links''')
    fhand.write('"links":[\n')

    count = 0
    for row in cur:
        if row[0] not in node_map or row[1] not in node_map: 
            continue
        if count > 0: 
            fhand.write(',\n')
        fhand.write('{"source":'+str(node_map[row[0]])+',"target":'+str(node_map[row[1]])+',"value":3}')  # Use node_map for source/target
        count += 1
    fhand.write(']};')

print("Open force.html in a browser to view the visualization")
cur.close()