from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import validators

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

INIT_URLS = ["https://www.foxnews.com",\
			"https://www.flickr.com",\
			"https://www.edx.org",\
			"https://en.wikipedia.org/wiki/Web_crawler"]

db_name = "search_index"
engine = create_engine(f"mysql://localhost/{ db_name }")
#session = Session(engine)

# Find hyperlinks in url
# Write hyperlinks to DB
def crawl(url):
	# Make request to url
	headers = {"User-Agent": "Mozilla/5.0 (compatible; Simplicitybot/1.0)"}
	request = Request(url, headers=headers)

	# Store response
	try:
		response = urlopen(request, timeout=4)
	except:
		return

	html_data = response.read()
	soup = BeautifulSoup(html_data, "html.parser")

	# Analyze response for hyperlinks
	urls = []
	for tmp_url in soup.find_all('a'):
		try:
			if tmp_url.get("href"):
				if validators.url(tmp_url.get("href")):
					urls.append(tmp_url.get("href"))
					continue
				urls.append(url + "/" + tmp_url.get("href"))
		except:
			continue
	if len(urls) == 0:
		return

	# Write to DB
	with engine.begin() as c:
		treferenced_weight = 1000 // len(urls)
		for url in urls:
			# If url does not exist in DB then add it
			if url:
				result = c.execute(text("SELECT url_id FROM url_info WHERE url = :url"), {"url": url}).all()
				if len(result) == 0:
					c.execute(text("INSERT INTO url_info (url, treferenced_weight)\
					VALUES (:url, :treferenced_weight)"),\
					{"url": url, "treferenced_weight": treferenced_weight})
				# Else update it's times column
				else:	
					c.execute(text("UPDATE url_info SET treferenced_weight = treferenced_weight + :treferenced_weight WHERE url = :url"),\
						{"url": url, "treferenced_weight": treferenced_weight})
	# Request robots.txt

	# Analyze robots.txt

	# Write to DB


# Analyze page:
# - Find keywords
# - Freshness of site
# Write to DB:
# - URL
# - Keyword list
# - Freshness (Date)
# - Language
def index(url):
	# TODO
	headers = {"User-Agent": "Mozilla/5.0 (compatible; Simplicitybot/1.0)"}
	request = Request(url, headers=headers)

	# Store response
	try:
		response = urlopen(request, timeout=5)
	except:
		return

	html_data = response.read()
	soup = BeautifulSoup(html_data, "html.parser")
	
	# Get keywords
	keywords = []
	try:
		for word in soup.title.string.strip().split():
			try:	
				keywords.append(word.lower())
			except:
				continue
	except:
		pass

	for tag in soup.find_all("h1"):
		if tag.string not in keywords:
			try:	
				keywords.append(tag.string.lower())
			except:
				continue

	# Insert word into keywords table
	with engine.begin() as c:
		for word in keywords:
			if word:
				c.execute(text("INSERT INTO keywords (url_id, word)\
					VALUES ((SELECT url_id FROM url_info WHERE url = :url), :word)"),\
					{"url": url, "word": word})

# Analyze user input:
# - Key words
# Look for key word list resemblance in DB
# Rank URLs obtained by closer resemblance of user input
def rank(query):
	return ["https://www.google.com"]