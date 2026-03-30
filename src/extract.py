import yaml
import feedparser
import requests
import logging
from datetime import datetime, timedelta
from time import mktime

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

# Realistic User-Agent to bypass CDNs
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def load_config(config_path="config/sources.yaml"):
    """
    Loads the YAML configuration file containing feeds and rules.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            logging.info("Configuration loaded successfully.")
            return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {config_path}")
        return None
    except Exception as e:
        logging.error(f"Error parsing YAML file: {e}")
        return None

def fetch_recent_articles(feeds_config, max_hours=72):
    """
    Fetches articles using 'requests' for HTTP robustness, then parses with 'feedparser'.
    """
    extracted_articles = []
    time_threshold = datetime.now() - timedelta(hours=max_hours)

    # Use a requests Session for better performance and consistent headers
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    for feed in feeds_config:
        logging.info(f"Fetching RSS feed: {feed['name']}")
        
        try:
            # 1. Fetch the raw XML string using the robust 'requests' library
            response = session.get(feed['url'], timeout=15)
            response.raise_for_status() # Raise error if HTTP fails (e.g., 404, 403)
            raw_xml = response.text
            
            # 2. Parse the raw string with feedparser
            parsed_feed = feedparser.parse(raw_xml)
            
            raw_entries_count = len(parsed_feed.entries)
            logging.info(f"--> Found {raw_entries_count} raw entries in {feed['name']}")
            
            for entry in parsed_feed.entries:
                published_dt = None
                
                # Robust date parsing
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_dt = datetime.fromtimestamp(mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_dt = datetime.fromtimestamp(mktime(entry.updated_parsed))
                
                # If a blog forgets to put a date, assume it's new
                if not published_dt:
                    logging.debug(f"Article '{entry.title}' has no date. Assuming it's new.")
                    published_dt = datetime.now()

                if published_dt >= time_threshold:
                    article_data = {
                        "title": entry.title,
                        "link": entry.link,
                        "summary": getattr(entry, 'summary', getattr(entry, 'description', 'No summary available.')),
                        "published_at": published_dt.isoformat(),
                        "source_name": feed['name'],
                        "category": feed['default_category'],
                        "source_weight": feed['weight']
                    }
                    extracted_articles.append(article_data)
                    
        except requests.exceptions.RequestException as req_err:
            logging.error(f"HTTP Request failed for {feed['name']}: {req_err}")
        except Exception as e:
            logging.error(f"Critical failure while processing feed {feed['name']}: {e}")

    logging.info(f"Extraction complete. Total recent articles found (last {max_hours}h): {len(extracted_articles)}")
    return extracted_articles

if __name__ == "__main__":
    # Test execution
    config = load_config()
    if config and "feeds" in config:
        recent_news = fetch_recent_articles(config["feeds"], max_hours=72)
        print(f"\nTest finished. Kept {len(recent_news)} articles.")