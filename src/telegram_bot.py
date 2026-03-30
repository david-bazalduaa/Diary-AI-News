import os
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

def format_message(articles, total_processed, duplicates_removed):
    """
    Formats the list of top articles into a clean Markdown string for Telegram.
    """
    if not articles:
        return "*Daily AI & ML Briefing*\n\nNo relevant news found today."

    # Header
    message = "*Daily AI & ML Briefing*\n"
    message += "_Here are the most relevant news of the day:_\n\n"

    # Body (Top News)
    for idx, article in enumerate(articles, start=1):
        title = article.get('title', 'No Title')
        summary = article.get('llm_summary', 'No summary available.')
        link = article.get('link', '#')
        category = article.get('category', 'General')
        score = article.get('score', 0)
        
        # We escape characters that might break Telegram's Markdown parsing
        # (Telegram's MarkdownV2 can be strict, but standard Markdown is easier for simple text)
        message += f"*{idx}\\. {title}*\n"
        message += f"{summary}\n"
        message += f"{category} \\| Score: {score}\n"
        message += f"🔗 [Read more]({link})\n\n"

    # Footer (Stats)
    message += "---\n"
    message += f"_Processed {total_processed} articles\\. Skipped {duplicates_removed} duplicates\\._"
    
    return message

def send_telegram_message(message):
    """
    Sends the formatted message to a specific Telegram chat/channel.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logging.error("Telegram credentials missing. Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown", # Enables bold, italics, and links
        "disable_web_page_preview": True # Keeps the chat clean without huge link previews
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes
        logging.info("Message sent successfully to Telegram!")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message to Telegram: {e}")
        # Log the exact error from Telegram if available
        if response is not None:
            logging.error(f"Telegram API Response: {response.text}")
        return False

if __name__ == "__main__":
    # Test execution (requires environment variables to be set)
    dummy_news = [
        {
            "title": "OpenAI drops new o1 model",
            "llm_summary": "A highly optimized model for reasoning tasks. Cheaper and faster than previous iterations.",
            "category": "LLMs",
            "score": 95,
            "link": "https://openai.com"
        }
    ]
    
    formatted_text = format_message(dummy_news, total_processed=45, duplicates_removed=5)
    print("--- Message Preview ---")
    print(formatted_text)
    
    # send_telegram_message(formatted_text) # Uncomment to actually send if env vars are set