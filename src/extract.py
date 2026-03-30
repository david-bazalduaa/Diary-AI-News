import yaml
import feedparser
import logging
from datetime import datetime, timedelta
from time import mktime

# Configure logging for production-level monitoring
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

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

def fetch_recent_articles(feeds_config, max_hours=24):
    """
    Fetches articles from a list of RSS feeds published within the specified timeframe.
    """
    extracted_articles = []
    time_threshold = datetime.utcnow() - timedelta(hours=max_hours)

    for feed in feeds_config:
        logging.info(f"Fetching RSS feed: {feed['name']}")
        
        try:
            # feedparser handles the HTTP request and XML parsing
            parsed_feed = feedparser.parse(feed['url'])
            
            # Check if the feed was fetched successfully
            if parsed_feed.bozo:
                logging.warning(f"Malformed XML in feed {feed['name']}, but attempting to parse anyway.")

            for entry in parsed_feed.entries:
                # Standardize publication date
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_dt = datetime.fromtimestamp(mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_dt = datetime.fromtimestamp(mktime(entry.updated_parsed))
                else:
                    logging.debug(f"Skipping article '{entry.title}' due to missing date.")
                    continue

                # Filter out old articles
                if published_dt >= time_threshold:
                    article_data = {
                        "title": entry.title,
                        "link": entry.link,
                        # Some feeds use 'description' instead of 'summary'
                        "summary": getattr(entry, 'summary', getattr(entry, 'description', '')),
                        "published_at": published_dt.isoformat(),
                        "source_name": feed['name'],
                        "category": feed['default_category'],
                        "source_weight": feed['weight']
                    }
                    extracted_articles.append(article_data)
                    
        except Exception as e:
            logging.error(f"Critical failure while processing feed {feed['name']}: {e}")

    logging.info(f"Extraction complete. Total recent articles found: {len(extracted_articles)}")
    return extracted_articles

if __name__ == "__main__":
    # Quick test execution
    config = load_config()
    
    if config and "feeds" in config:
        recent_news = fetch_recent_articles(config["feeds"], max_hours=24)
        
        if recent_news:
            print("\n--- Sample Extracted Article ---")
            print(f"Title: {recent_news[0]['title']}")
            print(f"Source: {recent_news[0]['source_name']}")
            print(f"Link: {recent_news[0]['link']}")
            print(f"Date: {recent_news[0]['published_at']}")