# CAP 931 – Sales Account Intelligence Agent

A Streamlit-based B2B sales-research prototype that turns public prospect website content, competitor webpages, and optional product notes into a structured account intelligence brief.

## Overview

The Sales Account Intelligence Agent supports sales representatives preparing for account research and outreach. The app collects product and prospect details, retrieves public webpage content, optionally processes competitor URLs and uploaded product notes, and sends the supplied information to an OpenAI model to create a concise, source-grounded sales brief.

If live OpenAI generation is unavailable because of an exhausted quota or billing issue, the app presents a clearly labeled fallback brief generated from the submitted inputs and retrieved webpage text.

## Features

- Streamlit form for sales-context input
- Required product name, category, value proposition, prospect URL, and target buyer fields
- Optional competitor URL list, one URL per line
- Optional product-document upload for `.txt`, `.md`, and `.pdf` files
- Public webpage retrieval with `requests`
- HTML parsing and visible-text extraction with BeautifulSoup
- PDF text extraction with PyPDF2
- Competitor webpage retrieval and inclusion in the research context
- Two prompt versions for prompt experimentation
- OpenAI-powered account brief generation using `gpt-4o-mini`
- Markdown download button for generated briefs
- Clear validation and fallback behavior for retrieval, parsing, and API errors

## Inputs

The interface accepts:

- **Product Name** — product being sold
- **Product Category** — category or market segment of the product
- **Value Proposition** — concise statement of customer value
- **Product Overview Upload** — optional `.txt`, `.md`, or `.pdf` document
- **Prospect Company Website** — public company website to research
- **Target Buyer** — intended sales contact or role
- **Competitor URLs** — optional list of competitor webpages, one per line
- **Prompt Version** — V2 assignment-aligned brief or V1 baseline brief

The app validates required fields, normalizes website URLs by adding `https://` when needed, and checks URL structure before retrieval.

## Output

### V2 — Assignment-Aligned Brief

The default V2 prompt generates an account intelligence brief with:

- Company Strategy
- Competitor Mentions
- Leadership Information
- Product/Strategy Summary
- Recommended Sales Angle
- Suggested Outreach Message
- Article Links

The outreach email is instructed to stay under 120 words. The app lists the prospect and competitor URLs used as sources.

### V1 — Baseline Brief

The V1 prompt provides a simpler baseline output:

- Prospect Snapshot
- Likely Business Focus
- Sales Angle
- Suggested Outreach Message
- Source Used

## Model Selection

The application uses `gpt-4o-mini` through the OpenAI Python SDK. This model was selected because it provides a practical balance of response quality, speed, and cost for a prototype that produces concise, structured sales-research briefs.

The prompts require the model to use only the supplied source material and state **“Not found in supplied source.”** when a requested detail is unsupported. This reduces unsupported claims and keeps the output tied to retrieved content.

## Prompt Experimentation

The project includes two prompt designs:

- **V1: Simple Brief** — a focused prompt that summarizes one prospect webpage into a basic sales brief.
- **V2: Assignment Aligned** — an expanded prompt that adds competitor research, uploaded product notes, leadership information, strategy analysis, recommended sales angles, and source URLs.

V2 is the default because it better aligns with the capstone requirement for a one-page account brief that addresses company strategy, competitors, leadership, product fit, and source links.

## Tech Stack

- Python 3.12+
- Streamlit
- OpenAI Python SDK
- requests
- BeautifulSoup4
- PyPDF2
- python-dotenv
- uv

## Project Structure

```text
CAP 931/
├── .gitignore
├── .python-version
├── app.py
├── pyproject.toml
├── README.md
├── uv.lock
└── src/
    └── cap_931/
        └── __init__.py
```

`.env` and `.venv/` are local-only files and should not be committed.

## Installation

This project uses `uv` for environment and dependency management.

```bash
uv sync
```

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
```

Do not commit `.env` to version control.

## Run the App

```bash
uv run streamlit run app.py
```

Then open the local Streamlit URL displayed in the terminal.

## How It Works

1. The user enters sales context in the Streamlit form.
2. The app validates required values and normalizes the prospect URL.
3. The app retrieves and extracts visible text from the prospect webpage.
4. The app optionally retrieves text from competitor webpages.
5. The app optionally extracts text from an uploaded `.txt`, `.md`, or `.pdf` product document.
6. The selected prompt version combines the supplied product, prospect, competitor, and document context.
7. OpenAI generates a Markdown account brief using `gpt-4o-mini`.
8. The user can review and download the brief as a Markdown file.
9. If an OpenAI quota or credit error occurs, the app displays a clearly labeled fallback brief instead.

## Error Handling

The application handles several common failure cases:

- Missing OpenAI API key
- Missing required form fields
- Invalid prospect URL
- Webpage retrieval failures
- Unsupported upload types
- PDF parsing issues
- OpenAI request failures
- OpenAI insufficient-quota or exhausted-credit responses

The fallback output is not presented as live AI generation. It is explicitly labeled so users understand the difference.

## Limitations

- The app reads public webpages that permit standard HTTP retrieval; some websites may block automated requests or require JavaScript rendering.
- Research depth is limited by the supplied prospect URL, competitor URLs, uploaded document, and text-length limits.
- The prototype does not independently search the web for news, annual reports, job postings, or 10-K filings.
- Live LLM output requires a valid OpenAI API key with available billing quota.
- The app is a prototype and should not be used as the sole basis for sales claims without human review.

## Future Enhancements

- Add web search for recent news, press releases, job postings, and investor filings
- Add per-finding citations and source snippets
- Add structured competitor comparison
- Add account monitoring and email alerts for selected keywords
- Add user authentication, rate limiting, logging, and secure production deployment
- Generate meeting briefs or presentation decks from approved research sources

## Author

Eduard Lukyanov