from threading import Thread
from essentials import crawl, index, engine, db_name, INIT_URLS
from sqlalchemy import create_engine, text
from time import sleep
import sys
import signal

#%#%#%#%#%#%#%#%#%#%#%#%#%
#% 	S I M P L I C I T Y %#
#%#%#%#%#%#%#%#%#%#%#%#%#%

def display_info():
    print()
    print("*" * 20 + " " * 5 + "simplicity".upper() + " " * 5 + "*" * 20)
    print()
    while True:
        with engine.connect() as c:
            # Sites crawled
            query = text("SELECT COUNT(url_id) FROM url_info WHERE crawled = 1")
            result = list(c.execute(query))
            num_crawled = result[0][0]

            # Sites not crawled
            query = text("SELECT COUNT(url_id) FROM url_info WHERE crawled = 0")
            result = list(c.execute(query))
            num_not_crawled = result[0][0]

            # Sites indexed
            query = text("SELECT COUNT(url_id) FROM url_info WHERE indexed = 1")
            result = list(c.execute(query))
            num_indexed = result[0][0]

            # Sites not indexed
            query = text("SELECT COUNT(url_id) FROM url_info WHERE indexed = 0")
            result = list(c.execute(query))
            num_not_indexed = result[0][0]

            to_print = "\rSites crawled: {} from {}\t\tSites indexed: {} from {}".format(num_crawled, num_not_crawled + num_crawled, num_indexed, num_indexed + num_not_indexed)

            sys.stdout.write(to_print)
            sys.stdout.flush()
            sleep(1)


# Crawler Thread
def crawler():
    while True:
        with engine.connect() as c:
            # Read url not crawled
            query = text("SELECT url FROM url_info WHERE crawled = 0 LIMIT 1")
            result = list(c.execute(query))
            
            # Check if value was retrieved
            if len(result) != 0:
                url = result[0]["url"]
            else:
                # TODO Log ig
                pass

            # Crawl url
            resp = crawl(url, c)

            # Indicate that it has been crawled
            if resp is None:
                query = text("UPDATE url_info SET crawled = 1 WHERE url = :url")
                query = query.bindparams(url=url)
                c.execute(query)
            else:
                #TODO
                pass

# Indexer Thread
def indexer():	
    while True:
        with engine.connect() as c:
            # Read url not indexed
            query = text("SELECT url_id, url FROM url_info WHERE indexed = 0 LIMIT 1")
            result = list(c.execute(query))

            # Check if response was not empty
            if len(result) != 0:
                url_id = result[0]["url_id"]
                url = result[0]["url"]
            else:
                # TODO
                # Log
                pass

            # Index url
            resp = index(url, url_id, c)

            # Set url as indexed
            if resp is None:
                query = text("UPDATE url_info SET indexed = 1 WHERE url = :url")
                query = query.bindparams(url=url)
                c.execute(query)
            else:
                # TODO
                pass

    
if __name__ == "__main__":       
    def signal_handler(sig, frame):
    	print("Exiting...")
    	exit(0)

    # Handle CTRL-C
    signal.signal(signal.SIGINT, signal_handler)

    # Create and initialize table
    with engine.connect() as c:
        query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = :db_name AND (table_name = 'url_info' OR table_name = 'keywords')")
        query = query.bindparams(db_name=db_name)

        result = c.execute(query)
        result = [table[0] for table in result]
        
        if len(result) != 2:
            # Drop all tables
            for table in result:
                query = text("DROP TABLE IF EXISTS :table")
                query = query.bindparams(table=table)
                c.execute(query)
            # Create tables from schema file
            with open("schema.sql") as f:
                schema = f.read().strip().split('\n')
                for line in schema:
                    query = text(line)
                    c.execute(query)

        # If table empty -> initialize with sample urls
        query = text("SELECT url_id FROM url_info")
        result = list(c.execute(query))
        if len(result) == 0:
            for url in INIT_URLS:
                query = text("INSERT INTO url_info (url) VALUES (:url)")
                query = query.bindparams(url=url)
                c.execute(query)
    
    # Create threads
    info = Thread(target=display_info)
    tcrawler = Thread(target=crawler)
    tindexer = Thread(target=indexer)

    # Start threads
    tcrawler.start()
    tindexer.start()	
    info.start()
