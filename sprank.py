import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('spider.sqlite')
cur = conn.cursor()

# Check the number of pages
cur.execute('SELECT COUNT(*) FROM Pages')
num_pages = cur.fetchone()[0]
if num_pages < 1:
    print("No pages found. Please run spider.py to crawl pages.")
    quit()

print(f"Found {num_pages} pages to rank.")

# Initialize ranks
cur.execute('SELECT id FROM Pages')
page_ids = [row[0] for row in cur]
ranks = {page_id: 1.0 for page_id in page_ids}  # Initialize all ranks to 1.0

iterations = int(input("Enter number of PageRank iterations (default is 20): ") or 20)
print(f"Running {iterations} iterations of PageRank.")

for i in range(iterations):
    print(f"Iteration {i + 1}")
    new_ranks = {page_id: 0 for page_id in page_ids}

    # Fetch links
    cur.execute('SELECT from_id, to_id FROM Links')
    links = cur.fetchall()

    if not links:
        print("No links found for PageRank calculation.")
        break

    # Create a dictionary to count outgoing links for each page
    outgoing_counts = {page_id: 0 for page_id in page_ids}
    for from_id, to_id in links:
        outgoing_counts[from_id] += 1

    # Distribute PageRank
    for from_id, to_id in links:
        if outgoing_counts[from_id] > 0:
            new_ranks[to_id] += ranks[from_id] / outgoing_counts[from_id]

    # Update ranks for normalization
    total_new_rank = sum(new_ranks.values())
    for page_id in page_ids:
        # Avoid division by zero; if total_new_rank is 0, we assign ranks evenly
        if total_new_rank > 0:
            new_ranks[page_id] /= total_new_rank
        else:
            new_ranks[page_id] = 1.0 / len(page_ids)  # Assign equal rank if total is zero

    ranks = new_ranks

    # Update ranks in the database
    for page_id, rank in ranks.items():
        cur.execute('UPDATE Pages SET new_rank=? WHERE id=?', (rank, page_id))

    conn.commit()

# Output final ranks
print(f"\nPageRank calculations complete after {iterations} iterations.")
print("\nFinal PageRanks:")
for page_id in sorted(page_ids, key=lambda id: ranks[id], reverse=True):
    print(f"{page_id} {ranks[page_id]:.12f}")

cur.close()