import sys
import logging
from extract import load_config, fetch_recent_articles
from process import score_articles, deduplicate_articles
from llm_summarizer import process_summaries
from telegram_bot import format_message, send_telegram_message

# Configure central logging for the entire pipeline
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # Ensure logs go to standard output for GitHub Actions
    ]
)

def main():
    """
    Main execution pipeline for the Daily AI News Bot.
    """
    logging.info("--- Starting Daily AI News Pipeline ---")

    # Step 1: Load Configuration
    config = load_config()
    if not config or 'feeds' not in config:
        logging.error("Failed to load configuration or no feeds defined. Exiting.")
        sys.exit(1)

    # Step 2: Extraction
    logging.info("Step 1/5: Extracting recent articles...")
    max_hours = 24
    raw_articles = fetch_recent_articles(config['feeds'], max_hours=max_hours)
    
    if not raw_articles:
        logging.warning("No new articles found in the last 24 hours. Exiting safely.")
        send_telegram_message("🤖 *Daily AI & ML Briefing*\n\nNo relevant news found today.")
        sys.exit(0)

    # Step 3: Scoring and Filtering
    logging.info("Step 2/5: Scoring articles based on keywords and source weights...")
    scored_articles = score_articles(raw_articles, config.get('keywords', {}))
    
    if not scored_articles:
        logging.warning("All articles were filtered out after scoring. Exiting safely.")
        sys.exit(0)

    # Step 4: Deduplication
    logging.info("Step 3/5: Removing semantic duplicates...")
    threshold = config.get('settings', {}).get('similarity_threshold', 0.85)
    unique_articles = deduplicate_articles(scored_articles, threshold=threshold)

    # Calculate statistics for the final message
    total_processed = len(raw_articles)
    duplicates_removed = len(raw_articles) - len(unique_articles)

    # Step 5: LLM Summarization (Enrichment)
    logging.info("Step 4/5: Generating AI summaries for the Top N articles...")
    top_n = config.get('settings', {}).get('max_articles_per_source', 5) # Let's limit to Top 5 total
    enriched_articles = process_summaries(unique_articles, top_n=top_n)

    # Step 6: Formatting and Delivery
    logging.info("Step 5/5: Formatting and sending to Telegram...")
    final_message = format_message(
        articles=enriched_articles, 
        total_processed=total_processed, 
        duplicates_removed=duplicates_removed
    )
    
    success = send_telegram_message(final_message)
    
    if success:
        logging.info("--- Pipeline Completed Successfully! ---")
    else:
        logging.error("--- Pipeline Finished with Delivery Errors ---")
        sys.exit(1)

if __name__ == "__main__":
    main()