#from urllib.request import Request, urlopen
import requests
from bs4 import BeautifulSoup
import validators
import re
from urllib.parse import urlparse, urlunparse
from nltk.corpus import stopwords

from sqlalchemy import create_engine, text

'''
INIT_URLS = ["https://www.foxnews.com",\
			"https://www.flickr.com",\
			"https://www.edx.org",\
			"https://en.wikipedia.org/wiki/Web_crawler"]
'''
INIT_URLS = ["https://web.archive.org/web/20080916124519/http://www.dmoz.org/"]


db_name = "search_index"
engine = create_engine(f"mysql://localhost/{ db_name }")
prog = re.compile(r"(?a)\W+")

# Find hyperlinks in url
# Write hyperlinks to DB
# Types of hyperlinks
# #<something>      -> Ignore
# /<uri component>  -> Append to current url and add
# <url>             -> Add as is
def crawl(url, c):
    # Make request to url
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Simplicitybot/1.0)"}

    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            # TODO 
            return None
    except:
        # Log and idk return
        # TODO 
        return None

    html_data = r.text
    soup = BeautifulSoup(html_data, "html.parser")

    # Analyze response for hyperlinks
    urls = []

    # Retrieve all a tags
    tags = soup.find_all("a")
    
    if len(tags) == 0:
        # TODO 
        # Send something idk
        return None
    
    for tag in tags:
        try:
            h_link = tag.get("href")
            # If href is a valid url append to urls
            if validators.url(h_link):
                urls.append(h_link)
            elif h_link[0] == "/":
                u = urlparse(url)
                h_link = urlunparse(u._replace(path=h_link))
                
                if url != h_link:
                    urls.append(h_link)
        except:
            continue 
    

    # If no urls found return
    if len(urls) == 0:
        # TODO 
        # Send something idk
        return None

    times_ref_weight = 1 / len(urls)
    
    # Insert every url to table
    for url in urls:
        query = text("SELECT url_id FROM url_info WHERE url = :url")
        query = query.bindparams(url=url)
        result = list(c.execute(query))

        # If url does not exist -> add it
        if len(result) == 0:
            query = text("INSERT INTO url_info (url, times_ref_weight) VALUES (:url, :times_ref_weight)")
            query = query.bindparams(url=url, times_ref_weight=times_ref_weight)
            c.execute(query)
            continue

        # Else increment its times_ref_weight value
        query = text("UPDATE url_info SET times_ref_weight = times_ref_weight + :times_ref_weight WHERE url = :url")
        query = query.bindparams(url=url, times_ref_weight=times_ref_weight)
        c.execute(query)

# Analyze page:
# - Find keywords
# - Freshness of site
# Write to DB:
# - URL
# - Keyword list
# - Freshness (Date)
# - Language
def index(url, url_id, c):
    # TODO
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Simplicitybot/1.0)"}

    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return None
    except:
        # TODO
        # Log or something idk yet
        return None

    html_data = r.text
    soup = BeautifulSoup(html_data, "html.parser")

    # Get keywords
    keywords = []
 
    # Get title from document
    title_tag = soup.find("title")
    if title_tag is not None:
        title = title_tag.string
        if title is not None:
            # RE
            # Only alphanumerical words
            words = title.split()
            for word in words:
                regexed_word = prog.sub('', word)
                if regexed_word != '':
                    keywords.append(regexed_word)

    # Get h1 from document
    h1_tag = soup.find("h1")
    if h1_tag is not None:
        h1 = h1_tag.string
        if h1 is not None:
            # RE
            # Only alphanumerical words
            words = h1.split()
            for word in words:
                regexed_word = prog.sub('', word)
                if regexed_word != '' and regexed_word not in keywords:
                    keywords.append(regexed_word)

	# Insert word into keywords table
    for keyword in keywords:
        query = text("INSERT INTO keywords (url_id, word) VALUES (:url_id, :word)")
        query = query.bindparams(url_id=url_id, word=keyword)
        c.execute(query)

# Analyze user input:
# - Key words
# Look for key word list resemblance in DB
# Rank URLs obtained by closer resemblance of user input
def rank(query):
    urls = []
    original_words = query.split()
    keywords = []
    s_w = [prog.sub("", word) for word in stopwords.words("english")]
    # Remove stopwords || Keep keywords
    for word in original_words:
        tmp_word = prog.sub('', word)
        if tmp_word != '' and tmp_word.lower() not in s_w:
            keywords.append(tmp_word)

    # Create dictionary of url_ids where the value is the times
    # it has been referenced by other words
    if len(keywords) != 0:
        url_ids = {}
        for keyword in keywords:
            with engine.connect() as c:
                query = text("SELECT keywords.url_id, url_info.times_ref_weight FROM keywords INNER JOIN url_info ON keywords.url_id = url_info.url_id WHERE LOWER(keywords.word) = :keyword ORDER BY url_info.times_ref_weight DESC LIMIT 10")
                query = query.bindparams(keyword=keyword)
                result = list(c.execute(query))

            for row in result:
                url_id = row["url_id"]
                times_ref_weight = row["times_ref_weight"]
                if url_id in url_ids:
                    url_ids[url_id]["times"] += 1
                    continue
                url_ids[url_id] = {"times": 1, "times_ref_weight": times_ref_weight}

        if len(url_ids) > 0 and len(url_ids) <= 10:
            for url_id in url_ids:
                with engine.connect() as c:
                    query = text("SELECT url FROM url_info WHERE url_id = :url_id")
                    query = query.bindparams(url_id=url_id)
                    result = list(c.execute(query))
                    url = result[0]["url"]
                    urls.append(url)
                
        elif len(url_ids) > 10:
            # Sort by times and limit to 10
            sorted_url_ids = sorted(url_ids, key=lambda x: url_ids[x]["times"], reverse=True)[0:10]

            for url_id in sorted_url_ids:
                del url_ids[url_id]

            sorted_url_ids = sorted(url_ids, key=lambda x: url_ids[x]["times_ref_weight"], reverse=True)
            for url_id in sorted_url_ids:
                with engine.connect() as c:
                    query = text("SELECT url FROM url_info WHERE url_id = :url_id")
                    query = query.bindparams(url_id=url_id)
                    result = list(c.execute(query))
                    url = result[0]["url"]
                    urls.append(url)

        else:
            return None

    else:
        return None

    return urls
