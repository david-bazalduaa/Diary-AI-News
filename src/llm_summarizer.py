import os
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

def setup_genai():
    """
    Initializes the Gemini API client using the environment variable.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY environment variable is missing.")
        return False
    
    genai.configure(api_key=api_key)
    return True

def generate_summary(title, content):
    """
    Calls the LLM to generate a concise, 2-line technical summary.
    """
    # System prompt / Context to enforce strict formatting
    prompt = f"""
    You are a Senior AI Engineer reading industry news. 
    Read the following article title and summary, and extract the core technical value.
    
    Rules:
    - Provide exactly 2 bullet points.
    - Be extremely concise (maximum 2 lines total).
    - Focus on the technical impact, release details, or business value.
    - Ignore marketing fluff.
    - Reply in Spanish.
    
    Title: {title}
    Content: {content}
    """
    
    try:
        # Using 1.5 Flash as it is fast and heavily subsidized (free tier)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Lower safety settings slightly to prevent false positives on tech news (e.g., "hacking", "cybersecurity")
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }
        
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return response.text.strip()
        
    except Exception as e:
        logging.error(f"Failed to generate LLM summary for '{title}': {e}")
        return None

def process_summaries(articles, top_n=5):
    """
    Takes the scored articles, slices the top N, and enriches them with LLM summaries.
    """
    if not setup_genai():
        logging.warning("Skipping LLM summarization due to missing API key. Falling back to original summaries.")
        return articles[:top_n]

    # We only want to spend API calls (and time) on the very best articles
    top_articles = articles[:top_n]
    logging.info(f"Generating LLM summaries for the top {len(top_articles)} articles.")
    
    for article in top_articles:
        llm_summary = generate_summary(article['title'], article.get('summary', ''))
        
        if llm_summary:
            # Replace the generic RSS summary with our custom AI summary
            article['llm_summary'] = llm_summary
        else:
            # Fallback if the API fails (e.g., timeout, quota limit)
            logging.debug(f"Falling back to original RSS summary for {article['title']}")
            article['llm_summary'] = article.get('summary', 'No summary available.')
            
    return top_articles

if __name__ == "__main__":
    # To test locally: export GEMINI_API_KEY="your_key_here"
    dummy_top_news = [
        {
            "title": "Meta releases Llama 3 weights", 
            "summary": "Meta has officially released the open weights for their new Llama 3 model, outperforming previous versions on multiple benchmarks.",
            "category": "Machine Learning / Open Source",
            "score": 85
        }
    ]
    
    enriched_news = process_summaries(dummy_top_news, top_n=1)
    print(f"\nTitle: {enriched_news[0]['title']}")
    print(f"AI Summary:\n{enriched_news[0].get('llm_summary')}")