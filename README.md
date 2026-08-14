# CAP 931 – Sales Account Intelligence Agent

This project is a Streamlit-based prototype that helps a sales representative generate a structured account brief from public prospect website content. It collects product and prospect information, retrieves public webpage text, and uses an OpenAI model to generate a concise sales-oriented summary. During testing, when the OpenAI account had insufficient quota, the app displayed a clearly labeled rule-based fallback brief so the workflow remained usable and transparent. [file:59]

## Overview

The Sales Account Intelligence Agent was built for the CAP 931 capstone project. The goal of the application is to support sales research by turning public prospect website information into a structured account brief that can help prepare outreach and account planning. The project was implemented in Python, uses Streamlit for the interface, and is managed with `uv` for reproducible dependency management. [file:59]

## Features

- Streamlit user interface for entering sales context. [file:59]
- Required inputs for product, prospect, and buyer information. [file:59]
- Optional competitor URL input. [file:59]
- Public webpage retrieval using `requests`. [file:59]
- HTML parsing and text extraction using BeautifulSoup. [file:59]
- LLM-based brief generation using OpenAI `gpt-4o-mini`. [file:59]
- Transparent fallback output when live AI generation cannot complete because of quota limits. [file:59]

## Inputs

The Streamlit interface accepts the following inputs:

- Product name [file:59]
- Product category [file:59]
- Value proposition [file:59]
- Prospect company website [file:59]
- Target buyer [file:59]
- Competitor URLs (optional) [file:59]

The application validates required fields, normalizes URLs by adding `https` when needed, and checks that the URL includes a valid scheme and network location before attempting retrieval. [file:59]

## Output

The application generates a structured account brief that includes:

- Prospect Snapshot [file:59]
- Likely Business Focus [file:59]
- Sales Angle [file:59]
- Suggested Outreach Message [file:59]
- Source Used [file:59]

The outreach message is intended to stay concise, and the prompt limits it to fewer than 120 words. [file:59]

## Tech Stack

- Python [file:59]
- Streamlit [file:59]
- requests [file:59]
- BeautifulSoup [file:59]
- OpenAI API [file:59]
- python-dotenv [file:59]
- uv [file:59]

## Project Structure

```bash
CAP 931/
├── .venv/
├── src/
│   └── cap_931/
│       └── __init__.py
├── .env
├── .gitignore
├── .python-version
├── app.py
├── pyproject.toml
├── README.md
└── uv.lock
```

## Installation

This project uses `uv` for dependency and environment management. The project configuration is stored in `pyproject.toml`, and locked dependencies are stored in `uv.lock`. [file:59]

Install dependencies with:

```bash
uv sync
```

If you are building the project manually, the report documents these package additions:

```bash
uv add streamlit requests beautifulsoup4
uv add openai python-dotenv
```

[file:59]

## Environment Variables

Create a `.env` file in the project root and add your OpenAI API key.

```env
OPENAIAPIKEY=your_api_key_here
```

The project report states that the application loads `OPENAIAPIKEY` from the `.env` file, so the environment variable name in your local setup should match the code exactly. [file:59]

## Run the App

Start the Streamlit application with:

```bash
uv run streamlit run app.py
```

During testing, the application launched successfully at the default local Streamlit address and accepted the required inputs. [file:59]

## How It Works

1. The user enters product, prospect, and buyer information in the Streamlit form. [file:59]
2. The app validates the required fields and normalizes the prospect URL. [file:59]
3. The app retrieves the public webpage using `requests` with a browser-like User-Agent header. [file:59]
4. BeautifulSoup parses the HTML and removes script, style, navigation, footer, header, and aside elements before extracting readable text. [file:59]
5. The page title and a truncated portion of the extracted text are passed into the prompt context. [file:59]
6. The app sends the structured prompt to OpenAI `gpt-4o-mini` to generate a concise account brief. [file:59]
7. If the OpenAI request fails because of insufficient quota, the app shows a clear warning and displays a rule-based fallback brief instead. [file:59]

## Prompt Strategy

The project uses a structured first-pass prompt design. The prompt defines the model’s role as a B2B sales research assistant, instructs it not to invent facts, includes labeled user inputs, includes the public webpage title and extracted text, and requests an exact Markdown output structure. [file:59]

This prompt is intended to ground the response in retrieved public content rather than producing a generic sales summary without evidence from the target website. [file:59]

## Error Handling

The application checks for the API key before continuing and catches both webpage retrieval errors and OpenAI request errors. [file:59]

When the OpenAI API returns an insufficient quota or exhausted credit condition, the app displays a clear user-facing warning instead of a raw technical error. In that case, a rule-based fallback brief is shown and explicitly labeled as generated without live AI. [file:59]

## Testing Notes

Testing confirmed the following workflow:

1. The Streamlit app launched successfully using `uv run streamlit run app.py`. [file:59]
2. The form accepted required product and prospect inputs. [file:59]
3. A Salesforce prospect webpage was retrieved successfully and the source information was displayed. [file:59]
4. The OpenAI request path was reached but returned a 429 insufficient-quota error because the API account had no credits remaining. [file:59]
5. The quota warning displayed clearly to the user. [file:59]
6. The fallback account brief generated successfully after the quota issue was handled. [file:59]

## Limitations

The main limitation observed during testing was exhausted OpenAI billing quota, which prevented full validation of the live LLM-generated brief output. The fallback path preserved the end-to-end demonstration, but it should be described accurately as contingency output rather than live AI output. [file:59]

The report also identifies future improvements such as competitor mention extraction, leadership information extraction, source citations per finding, prompt comparisons, and production deployment controls. [file:59]

## Commands Used

```bash
uv add streamlit requests beautifulsoup4
uv add openai python-dotenv
uv tree
uv run streamlit run app.py
```

[file:59]

## Author

Eduard Lukyanov