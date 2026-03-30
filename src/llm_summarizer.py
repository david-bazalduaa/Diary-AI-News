import os
import logging
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

def generate_summary(title, content):
    """
    Calls the new Gemini API client to generate a concise, 2-line technical summary.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY environment variable is missing.")
        return None

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
        # Initialize the new client
        client = genai.Client(api_key=api_key)
        
        # Call the model using the updated 2026 syntax
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3 # Keep responses deterministic and professional
            )
        )
        return response.text.strip()
        
    except Exception as e:
        logging.error(f"Failed to generate LLM summary for '{title}': {e}")
        return None

def process_summaries(articles, top_n=5):
    """
    Takes the scored articles, slices the top N, and enriches them with LLM summaries.
    """
    top_articles = articles[:top_n]
    logging.info(f"Generating LLM summaries for the top {len(top_articles)} articles.")
    
    for article in top_articles:
        llm_summary = generate_summary(article['title'], article.get('summary', ''))
        
        if llm_summary:
            article['llm_summary'] = llm_summary
        else:
            logging.debug(f"Falling back to original RSS summary for {article['title']}")
            article['llm_summary'] = article.get('summary', 'No summary available.')
            
    return top_articles