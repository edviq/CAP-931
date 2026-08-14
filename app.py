import os
import io
from urllib.parse import urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None


load_dotenv()

st.set_page_config(
    page_title="Sales Account Intelligence Agent",
    page_icon="🎯",
    layout="wide",
)

api_key = os.getenv("OPENAI_API_KEY")

st.title("Sales Account Intelligence Agent")
st.caption("Workflow: Intake agent → Web research agent → Brief generation agent.")

if not api_key:
    st.error("OPENAI_API_KEY was not found. Check your .env file.")
    st.stop()

client = OpenAI(api_key=api_key)

st.write(
    "Enter product, prospect, competitor, and optional product-document details "
    "to create a research-based sales account brief."
)


def normalize_url(url: str) -> str:
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


def extract_webpage_text(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Sales Account Intelligence Agent)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        page_title = soup.title.get_text(strip=True) if soup.title else "Untitled page"
        page_text = " ".join(soup.get_text(" ", strip=True).split())

        return {
            "success": True,
            "title": page_title,
            "text": page_text[:5000],
            "url": url,
            "message": "Webpage retrieved successfully.",
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "title": "",
            "text": "",
            "url": url,
            "message": f"Could not retrieve webpage: {error}",
        }


def parse_competitor_urls(raw_text: str) -> list[str]:
    if not raw_text.strip():
        return []

    urls = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        normalized = normalize_url(line)
        if is_valid_url(normalized):
            urls.append(normalized)

    return urls


def collect_competitor_research(competitor_urls: list[str]) -> tuple[str, list[str]]:
    research_blocks = []
    source_urls = []

    for url in competitor_urls:
        result = extract_webpage_text(url)
        source_urls.append(url)

        if result["success"]:
            research_blocks.append(
                f"COMPETITOR URL: {url}\n"
                f"TITLE: {result['title']}\n"
                f"TEXT: {result['text']}"
            )
        else:
            research_blocks.append(
                f"COMPETITOR URL: {url}\n"
                f"ERROR: {result['message']}"
            )

    if not research_blocks:
        return "Not found in supplied source.", []

    return "\n\n".join(research_blocks)[:8000], source_urls


def extract_uploaded_file_text(uploaded_file) -> str:
    if uploaded_file is None:
        return "Not found in supplied source."

    try:
        file_name = uploaded_file.name.lower()

        if file_name.endswith(".txt") or file_name.endswith(".md"):
            text = uploaded_file.read().decode("utf-8", errors="ignore")
            return text[:4000] if text.strip() else "Not found in supplied source."

        if file_name.endswith(".pdf"):
            if PdfReader is None:
                return (
                    "PDF file uploaded but PDF parsing library is not available. "
                    "The file was received but could not be parsed in this environment."
                )

            pdf_bytes = io.BytesIO(uploaded_file.read())
            reader = PdfReader(pdf_bytes)
            pages = []

            for page in reader.pages[:10]:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)

            combined = "\n".join(pages).strip()
            return combined[:4000] if combined else "Not found in supplied source."

        return (
            f"Uploaded file '{uploaded_file.name}' was received, but this prototype "
            f"currently parses only .txt, .md, and .pdf files."
        )

    except Exception as error:
        return f"Could not parse uploaded file: {error}"


def build_prompt_v1(
    product_name,
    product_category,
    value_proposition,
    prospect_url,
    target_buyer,
    webpage_title,
    webpage_text,
):
    return f"""
You are a B2B sales research assistant.

Create a concise one-page sales account brief using only the information provided below.
Do not invent facts. If something is not supported by the source text, say "Not found in supplied source."

PRODUCT NAME:
{product_name}

PRODUCT CATEGORY:
{product_category}

VALUE PROPOSITION:
{value_proposition}

PROSPECT URL:
{prospect_url}

TARGET BUYER:
{target_buyer}

WEBPAGE TITLE:
{webpage_title}

PUBLIC WEBPAGE TEXT:
{webpage_text}

Return the output in Markdown with these sections:

# Account Brief
## Prospect Snapshot
## Likely Business Focus
## Sales Angle
## Suggested Outreach Message
## Source Used

For Suggested Outreach Message, write a short personalized outreach email under 120 words.
"""


def build_prompt_v2(
    product_name,
    product_category,
    value_proposition,
    prospect_url,
    target_buyer,
    webpage_title,
    webpage_text,
    competitor_text,
    uploaded_text,
    article_links_text,
):
    return f"""
You are a careful B2B sales research assistant.

Use only the supplied source material.
Do not invent facts.
If something is not supported by the supplied sources, write:
"Not found in supplied source."

Create a concise one-page account intelligence brief in Markdown.

INPUTS
Product Name: {product_name}
Product Category: {product_category}
Value Proposition: {value_proposition}
Prospect URL: {prospect_url}
Target Buyer: {target_buyer}

Prospect Page Title:
{webpage_title}

Prospect Source Text:
{webpage_text}

Competitor Source Text:
{competitor_text}

Uploaded Product Notes:
{uploaded_text}

Source URLs:
{article_links_text}

Return exactly these sections:

# Account Intelligence Brief

## Company Strategy
Summarize the prospect companys strategy and relevant industry activity based only on supplied text.
Mention executive statements, hiring signals, press-release-like information, or technology clues if present.

## Competitor Mentions
Identify any mentions or likely overlaps involving the supplied competitors based only on the supplied source material.
If none are found, say "Not found in supplied source."

## Leadership Information
List key leaders or quoted executives found in the supplied sources and briefly explain why they may matter.

## Product/Strategy Summary
Explain how the prospect’s visible strategy may connect to the product value proposition.
If public-company-style strategy signals are not present, say "Not found in supplied source."

## Recommended Sales Angle
Give 2 to 3 short bullets tailored to the target buyer.

## Suggested Outreach Message
Write a short personalized outreach email under 120 words.

## Article Links
List the source URLs used for the brief as bullet points.
"""


def generate_account_brief(prompt_style, **kwargs) -> str:
    if prompt_style == "V1":
        prompt = build_prompt_v1(
            product_name=kwargs["product_name"],
            product_category=kwargs["product_category"],
            value_proposition=kwargs["value_proposition"],
            prospect_url=kwargs["prospect_url"],
            target_buyer=kwargs["target_buyer"],
            webpage_title=kwargs["webpage_title"],
            webpage_text=kwargs["webpage_text"],
        )
    else:
        prompt = build_prompt_v2(
            product_name=kwargs["product_name"],
            product_category=kwargs["product_category"],
            value_proposition=kwargs["value_proposition"],
            prospect_url=kwargs["prospect_url"],
            target_buyer=kwargs["target_buyer"],
            webpage_title=kwargs["webpage_title"],
            webpage_text=kwargs["webpage_text"],
            competitor_text=kwargs["competitor_text"],
            uploaded_text=kwargs["uploaded_text"],
            article_links_text=kwargs["article_links_text"],
        )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are careful, concise, and do not invent unsupported facts."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


def generate_fallback_brief_v2(
    product_name,
    product_category,
    value_proposition,
    prospect_url,
    target_buyer,
    webpage_title,
    webpage_text,
    competitor_urls,
    uploaded_text,
    article_links_text,
) -> str:
    snippet = webpage_text[:900] if webpage_text else "Not found in supplied source."
    competitors_display = (
        "\n".join(f"- {url}" for url in competitor_urls)
        if competitor_urls
        else "Not found in supplied source."
    )
    uploaded_summary = uploaded_text[:700] if uploaded_text else "Not found in supplied source."

    return f"""
# Account Intelligence Brief

## Company Strategy
Based on the retrieved public webpage text from **{webpage_title}**, the company appears to focus on:
{snippet}

## Competitor Mentions
Supplied competitor URLs:
{competitors_display}

Direct competitor mentions in the supplied source: Not found in supplied source.

## Leadership Information
Not found in supplied source.

## Product/Strategy Summary
**{product_name}** is a **{product_category}** offering.
Value proposition: {value_proposition}

This may be relevant to a **{target_buyer}** if the prospect is focused on the business areas described in the public webpage content.

Uploaded product notes summary:
{uploaded_summary}

## Recommended Sales Angle
- Connect {product_name} to the prospect’s visible website priorities.
- Tailor messaging to the {target_buyer} using the stated value proposition.
- Use public website content as the basis for personalized outreach.

## Suggested Outreach Message
Hi — I reviewed your website and noticed your organization is focused on initiatives related to the areas highlighted on your public-facing page. I believe {product_name} could support a {target_buyer} by improving how teams use research and account insights to drive more personalized outreach. If helpful, I’d be glad to share a short example tailored to your business context.

## Article Links
{article_links_text}

---
*Fallback brief generated from supplied inputs and retrieved webpage text because live AI generation was unavailable.*
"""


with st.form("sales_agent_form"):
    st.subheader("Product Information")

    product_name = st.text_input(
        "Product Name *",
        placeholder="Example: InsightFlow AI",
    )

    product_category = st.text_input(
        "Product Category *",
        placeholder="Example: AI-powered sales intelligence platform",
    )

    value_proposition = st.text_area(
        "Value Proposition *",
        placeholder=(
            "Example: Helps sales teams turn public account signals "
            "into personalized outreach."
        ),
    )

    uploaded_file = st.file_uploader(
        "Upload product overview sheet or deck (optional)",
        type=["txt", "md", "pdf"],
        help="This prototype parses .txt, .md, and .pdf files.",
    )

    st.subheader("Prospect Information")

    prospect_url = st.text_input(
        "Prospect Company Website *",
        placeholder="https://www.example.com",
    )

    target_buyer = st.text_input(
        "Target Buyer *",
        placeholder="Example: VP of Sales Operations",
    )

    competitor_urls_raw = st.text_area(
        "Competitor URLs (optional)",
        placeholder="Enter one URL per line",
    )

    st.subheader("Prompt Experimentation")

    prompt_style = st.selectbox(
        "Prompt Version",
        options=["V2 - Assignment Aligned", "V1 - Simple Brief"],
        index=0,
        help=(
            "Use V2 for the rubric-aligned one-pager. "
            "V1 is included as an experimentation baseline."
        ),
    )

    submitted = st.form_submit_button("Generate Account Brief")


if submitted:
    required_fields = [
        product_name,
        product_category,
        value_proposition,
        prospect_url,
        target_buyer,
    ]

    if not all(field.strip() for field in required_fields):
        st.error("Please complete every field marked with an asterisk (*).")
    else:
        prospect_url = normalize_url(prospect_url)

        if not is_valid_url(prospect_url):
            st.error("Please enter a valid prospect company website URL.")
        else:
            competitor_urls = parse_competitor_urls(competitor_urls_raw)
            uploaded_text = extract_uploaded_file_text(uploaded_file)

            with st.spinner("Retrieving public webpage content..."):
                research = extract_webpage_text(prospect_url)

            if not research["success"]:
                st.error(research["message"])
            else:
                with st.spinner("Retrieving competitor webpages..."):
                    competitor_text, competitor_source_urls = collect_competitor_research(
                        competitor_urls
                    )

                source_urls = [prospect_url] + competitor_source_urls
                deduped_source_urls = []
                for url in source_urls:
                    if url not in deduped_source_urls:
                        deduped_source_urls.append(url)

                article_links_text = (
                    "\n".join(f"- {url}" for url in deduped_source_urls)
                    if deduped_source_urls
                    else "Not found in supplied source."
                )

                st.success(research["message"])

                st.write("### Research Sources")
                st.write(f"**Prospect page title:** {research['title']}")
                st.write(f"**Prospect URL:** {prospect_url}")

                if competitor_urls:
                    st.write("**Competitor URLs provided:**")
                    for url in competitor_urls:
                        st.write(f"- {url}")

                if uploaded_file is not None:
                    st.write(f"**Uploaded file:** {uploaded_file.name}")

                selected_prompt_key = "V2" if prompt_style.startswith("V2") else "V1"
                st.write(f"**Prompt version used:** {selected_prompt_key}")

                with st.spinner("Generating sales account brief..."):
                    try:
                        brief = generate_account_brief(
                            prompt_style=selected_prompt_key,
                            product_name=product_name,
                            product_category=product_category,
                            value_proposition=value_proposition,
                            prospect_url=prospect_url,
                            target_buyer=target_buyer,
                            webpage_title=research["title"],
                            webpage_text=research["text"],
                            competitor_text=competitor_text,
                            uploaded_text=uploaded_text,
                            article_links_text=article_links_text,
                        )

                        st.write("## Generated Account Brief")
                        st.markdown(brief)

                        st.download_button(
                            "Download Brief as Markdown",
                            data=brief,
                            file_name="account_brief.md",
                            mime="text/markdown",
                        )

                    except Exception as error:
                        error_text = str(error)

                        if (
                            "insufficient_quota" in error_text
                            or "credit_balance_exhausted" in error_text
                        ):
                            st.warning(
                                "OpenAI billing quota is exhausted. "
                                "Showing a fallback brief generated from supplied inputs "
                                "and retrieved public webpage content."
                            )

                            fallback_brief = generate_fallback_brief_v2(
                                product_name=product_name,
                                product_category=product_category,
                                value_proposition=value_proposition,
                                prospect_url=prospect_url,
                                target_buyer=target_buyer,
                                webpage_title=research["title"],
                                webpage_text=research["text"],
                                competitor_urls=competitor_urls,
                                uploaded_text=uploaded_text,
                                article_links_text=article_links_text,
                            )

                            st.write("## Generated Account Brief")
                            st.markdown(fallback_brief)

                            st.download_button(
                                "Download Fallback Brief as Markdown",
                                data=fallback_brief,
                                file_name="account_brief_fallback.md",
                                mime="text/markdown",
                            )
                        else:
                            st.error(f"OpenAI request failed: {error}")