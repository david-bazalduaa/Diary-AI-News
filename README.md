# Automated AI/ML News ETL Pipeline

## Overview
This repository contains a serverless, automated Extract, Transform, Load (ETL) pipeline designed to aggregate, filter, deduplicate, and summarize the latest Artificial Intelligence and Machine Learning news. The system operates autonomously, running daily via Continuous Integration (CI) schedules, and delivers a highly curated briefing to a designated communication channel.

Built with a focus on cost-efficiency, reliability, and modularity, this project demonstrates end-to-end data engineering, Natural Language Processing (NLP), and API integration without relying on paid infrastructure or commercial API tiers.

## Architecture & Engineering Decisions

The pipeline is divided into five distinct stages, orchestrated by a central execution script:

1. **Extraction (`src/extract.py`):**
   - Utilizes `requests` with custom User-Agent headers to reliably bypass basic CDN protections (e.g., Cloudflare) commonly found on technology blogs.
   - Parses XML/RSS feeds using `feedparser`, implementing robust fallback mechanisms for inconsistent timestamp formats across different publishers.

2. **Transformation & Scoring (`src/process.py`):**
   - **Keyword-Based Weighting:** Evaluates raw text against a predefined matrix of positive (e.g., "MLOps", "LLM", "RAG") and negative (e.g., "Crypto", "Politics") keywords to calculate a relevance score.
   - **Semantic Deduplication:** Instead of relying on expensive third-party embedding APIs, the system uses `scikit-learn`'s `TfidfVectorizer` and Cosine Similarity to mathematically identify and remove duplicate coverage of the same event across multiple sources.

3. **Enrichment (`src/llm_summarizer.py`):**
   - Integrates with the `google-genai` SDK to leverage the Gemini 1.5 Flash model. 
   - Utilizes strict prompt engineering to force the LLM to output concise, technical bullet points, stripping away marketing language and focusing purely on the engineering or business impact.
   - Implements graceful degradation: if the LLM API rate limits are reached or the service is unavailable, the system falls back to the original RSS summary rather than failing the execution.

4. **Delivery (`src/telegram_bot.py`):**
   - Formats the processed data into strict Markdown.
   - Executes a REST POST request to the Telegram Bot API to deliver the final briefing. Link previews are intentionally disabled to maintain a clean UI on mobile devices.

5. **Orchestration (`src/main.py` & `.github/workflows`):**
   - The entire workflow is executed daily using GitHub Actions cron schedules, achieving a 100% serverless and zero-maintenance deployment.

## Technology Stack

* **Language:** Python 3.11+
* **Machine Learning & NLP:** Scikit-learn (TF-IDF, Cosine Similarity)
* **Generative AI:** Google GenAI SDK (Gemini 1.5 Flash)
* **Data Extraction:** Requests, Feedparser
* **Infrastructure:** GitHub Actions (Ubuntu environments)

## Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── daily_run.yml       # CI/CD pipeline configuration
├── config/
│   └── sources.yaml            # RSS feeds, source weights, and keyword rules
├── src/
│   ├── extract.py              # Data ingestion module
│   ├── process.py              # NLP scoring and deduplication module
│   ├── llm_summarizer.py       # LLM integration module
│   ├── telegram_bot.py         # Delivery module
│   └── main.py                 # Pipeline orchestrator
├── requirements.txt            # Python dependencies
└── README.md
```

## Setup and Local Development

### 1. Clone the repository
```bash
git clone [https://github.com/yourusername/ai-news-etl.git](https://github.com/yourusername/ai-news-etl.git)
cd ai-news-etl
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
The system requires the following environment variables to function correctly. Create a `.env` file or export them directly in your terminal:

```bash
export GEMINI_API_KEY="your_google_ai_studio_key"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_telegram_chat_id"
```

### 5. Run the pipeline
```bash
python src/main.py
```

## Configuration

The `config/sources.yaml` file acts as the control plane for the pipeline. You can add new RSS feeds, adjust the domain authority weight of specific sources, or update the keyword tracking lists without modifying the core Python logic.

## Deployment

This project is configured for automated deployment via GitHub Actions.
1. Navigate to your GitHub repository settings.
2. Go to **Secrets and variables > Actions**.
3. Add `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID` as Repository Secrets.
4. The workflow will automatically trigger based on the cron schedule defined in `.github/workflows/daily_run.yml`. You can also trigger it manually via the Actions tab.
