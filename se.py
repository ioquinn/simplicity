from threading import Thread
from essentials import crawl, index, engine, INIT_URLS
from sqlalchemy import create_engine, text
from time import sleep
from sys import exit
import signal

#%#%#%#%#%#%#%#%#%#%#%#%#%
#% 	S I M P L I C I T Y %#
#%#%#%#%#%#%#%#%#%#%#%#%#%

# Crawler Thread
def crawler():
	while True:
		with engine.connect() as c:
			# Read from DB values not crawled
			urls = c.execute(text("SELECT url FROM url_info WHERE crawled = 0"))
			urls = [row["url"] for row in urls]

			# Show alert if all sites have been crawled
			if len(urls) == 0:
				print("NO MORE SITES TO CRAWL, WEB ENDED")
				return 0

			# Iterate through these running crawl on each site
			# and switching the "crawled" column once crawled
			for url in urls:
				crawl(url)
				c.execute(text("UPDATE url_info SET crawled = 1 WHERE url = :url"), {"url": url})

# Indexer Thread
def indexer():	
	while True:
		# Read from DB values not indexed
		with engine.connect() as c:
			urls = c.execute(text("SELECT url FROM url_info WHERE indexed = 0"))
			urls = [row["url"] for row in urls]

			# Show alert if all sites have been crawled
			if len(urls) == 0:
				print("NO MORE SITES TO INDEX, KEEP CRAWLING")
				return 0

			# Iterate through these running crawl on each site
			# and switching the "crawled" column once crawled
			for url in urls:
				index(url)
				c.execute(text("UPDATE url_info SET indexed = 1 WHERE url = :url"), {"url": url})			

def signal_handler(sig, frame):
	print("Exiting...")
	exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Initiliaze table "Sites"
with engine.begin() as c:
	# Check database/tables existence
	# If doesn't exist create

	# If table empty -> initialize with sample urls
	if len(c.execute(text("SELECT * FROM url_info")).all()) == 0:
		for URL in INIT_URLS:
			c.execute(text("INSERT INTO url_info (url)\
				VALUES (:url)"), {"url": URL})

tcrawler = Thread(target=crawler)
tindexer = Thread(target=indexer)
tcrawler.start()
tindexer.start()	