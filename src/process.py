import re
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

def calculate_score(article, keywords_config):
    """
    Calculates a relevance score based on source weight and keyword presence.
    """
    # Start with the base weight assigned to the source in YAML
    score = article.get('source_weight', 0)
    
    # Combine title and summary for keyword searching, converted to lowercase
    text_to_search = f"{article.get('title', '')} {article.get('summary', '')}".lower()
    
    positive_kws = keywords_config.get('positive', [])
    negative_kws = keywords_config.get('negative', [])
    
    # Add points for positive keywords (using regex for exact word boundaries)
    for kw in positive_kws:
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_to_search):
            score += 15  # Arbitrary boost per positive keyword

    # Subtract points for negative keywords (penalize hype/noise)
    for kw in negative_kws:
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_to_search):
            score -= 50  # Heavy penalty for negative keywords

    return score

def score_articles(articles, keywords_config):
    """
    Applies the scoring function to a list of articles and filters out low-value ones.
    """
    scored_articles = []
    for article in articles:
        article['score'] = calculate_score(article, keywords_config)
        
        # Only keep articles with a positive score (filter out the heavy negative ones)
        if article['score'] > 0:
            scored_articles.append(article)
            
    # Sort by score descending
    scored_articles.sort(key=lambda x: x['score'], reverse=True)
    logging.info(f"Scored {len(scored_articles)} articles. Top score: {scored_articles[0]['score'] if scored_articles else 0}")
    
    return scored_articles

def deduplicate_articles(articles, threshold=0.85):
    """
    Removes semantically similar articles using TF-IDF and Cosine Similarity,
    keeping the one with the highest score.
    """
    if not articles:
        return []

    # Extract just the titles for comparison
    titles = [article['title'] for article in articles]
    
    # Vectorize titles
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform(titles)
    except ValueError:
        # Happens if titles list is empty or only contains stop words
        logging.warning("TF-IDF Vectorizer failed (possibly empty text). Skipping deduplication.")
        return articles

    # Calculate similarity matrix
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    indices_to_drop = set()
    num_articles = len(articles)

    for i in range(num_articles):
        if i in indices_to_drop:
            continue
        for j in range(i + 1, num_articles):
            if j in indices_to_drop:
                continue
            
            # If similarity is above our threshold
            if cosine_sim[i][j] >= threshold:
                # Keep the one with the higher score, drop the other
                if articles[i]['score'] >= articles[j]['score']:
                    indices_to_drop.add(j)
                    logging.debug(f"Dropped '{articles[j]['title']}' as duplicate of '{articles[i]['title']}'")
                else:
                    indices_to_drop.add(i)
                    logging.debug(f"Dropped '{articles[i]['title']}' as duplicate of '{articles[j]['title']}'")
                    break # i is dropped, move to next i

    # Build the final unique list
    unique_articles = [article for idx, article in enumerate(articles) if idx not in indices_to_drop]
    
    logging.info(f"Deduplication complete. Kept {len(unique_articles)} out of {num_articles} articles.")
    return unique_articles

if __name__ == "__main__":
    # Dummy test to verify logic
    dummy_articles = [
        {"title": "OpenAI releases new o1-mini model", "summary": "A fast LLM.", "source_weight": 50},
        {"title": "OpenAI launches o1-mini fast model", "summary": "New release.", "source_weight": 30}, # Duplicate
        {"title": "Bitcoin hits record high", "summary": "Crypto market rallies.", "source_weight": 40}   # Should be penalized
    ]
    
    dummy_keywords = {
        "positive": ["llm", "release"],
        "negative": ["crypto", "bitcoin"]
    }
    
    scored = score_articles(dummy_articles, dummy_keywords)
    print("After Scoring:")
    for a in scored: print(f"- {a['title']} (Score: {a['score']})")
        
    final_list = deduplicate_articles(scored, threshold=0.6) # Lower threshold for tiny dummy dataset
    print("\nAfter Deduplication:")
    for a in final_list: print(f"- {a['title']}")