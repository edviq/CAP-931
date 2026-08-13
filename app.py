import os
import streamlit as st
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from urllib.parse import urlparse

load_dotenv()

st.set_page_config(
    page_title="Sales Account Intelligence Agent",
    page_icon="🎯",
    layout="wide",
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def normalize_url(url):
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)

def extract_webpage_text(url):
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
            "message": "Webpage retrieved successfully.",
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "title": "",
            "text": "",
            "message": f"Could not retrieve webpage: {error}",
        }

def generate_fallback_brief(product_name, product_category, value_proposition,
                            prospect_url, target_buyer, webpage_title, webpage_text):
    snippet = webpage_text[:700] if webpage_text else "Not found in supplied source."

    return f"""
# Account Brief

## Prospect Snapshot
The prospect website reviewed was **{webpage_title}** at {prospect_url}.

## Likely Business Focus
Based on the retrieved public webpage content, the company appears to focus on:
{snippet}

## Sales Angle
**{product_name}** is a **{product_category}** that may be relevant to a **{target_buyer}**.
Primary value proposition: {value_proposition}

## Suggested Outreach Message
Hi — I reviewed your website and noticed your organization is focused on initiatives related to the areas highlighted on your public-facing page. I believe {product_name} could support a {target_buyer} by improving how teams use research and account insights to drive more personalized outreach. If helpful, I’d be glad to share a short example tailored to your business context.

## Source Used
Fallback brief generated from the retrieved public webpage text because live AI generation was unavailable.
"""

def generate_account_brief(product_name, product_category, value_proposition,
                           prospect_url, target_buyer, webpage_title, webpage_text):
    prompt = f"""
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

st.title("Sales Account Intelligence Agent")

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY was not found. Check your .env file.")
    st.stop()

st.write(
    "Enter product and prospect details to create a research-based sales account brief."
)

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

    st.subheader("Prospect Information")

    prospect_url = st.text_input(
        "Prospect Company Website *",
        placeholder="https://www.example.com",
    )

    target_buyer = st.text_input(
        "Target Buyer *",
        placeholder="Example: VP of Sales Operations",
    )

    competitor_urls = st.text_area(
        "Competitor URLs (optional)",
        placeholder="Enter one URL per line",
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
            with st.spinner("Retrieving public webpage content..."):
                research = extract_webpage_text(prospect_url)

            if not research["success"]:
                st.error(research["message"])
            else:
                st.success(research["message"])

                st.write("### Research Source")
                st.write(f"**Page title:** {research['title']}")
                st.write(f"**URL:** {prospect_url}")

                with st.spinner("Generating sales account brief..."):
                    try:
                        brief = generate_account_brief(
                            product_name=product_name,
                            product_category=product_category,
                            value_proposition=value_proposition,
                            prospect_url=prospect_url,
                            target_buyer=target_buyer,
                            webpage_title=research["title"],
                            webpage_text=research["text"],
                        )

                        st.write("## Generated Account Brief")
                        st.markdown(brief)

                    except Exception as error:
                        error_text = str(error)

                        if "insufficient_quota" in error_text or "credit_balance_exhausted" in error_text:
                            st.warning(
                                "OpenAI billing quota is exhausted. "
                                "Showing a fallback brief generated from retrieved public webpage content."
                            )

                            fallback_brief = generate_fallback_brief(
                                product_name=product_name,
                                product_category=product_category,
                                value_proposition=value_proposition,
                                prospect_url=prospect_url,
                                target_buyer=target_buyer,
                                webpage_title=research["title"],
                                webpage_text=research["text"],
                            )

                            st.write("## Generated Account Brief")
                            st.markdown(fallback_brief)
                        else:
                            st.error(f"OpenAI request failed: {error}")