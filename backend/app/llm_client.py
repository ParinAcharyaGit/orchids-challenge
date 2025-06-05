# backend/app/llm_client.py
# LLM + prompt template for the website cloner with CSS optimization
# TO DO: Add support for other LLM providers

import os, re
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
import json
from groq import Groq

load_dotenv() 

GROQ_API_KEY = os.getenv("GROQ_API_KEY", None)
if not GROQ_API_KEY:
    raise RuntimeError("Missing Groq API Key")

client = Groq(api_key=GROQ_API_KEY)

MODEL_ID = "llama-3.3-70b-versatile"

def truncate_css(css_text: str, max_chars: int = 15000) -> str:
    """
    Intelligently truncate CSS while preserving important styles
    """
    if len(css_text) <= max_chars:
        return css_text
    
    print(f"🎨 CSS too long ({len(css_text)} chars), truncating to {max_chars} chars...")
    
    # Split CSS into rules
    css_rules = []
    current_rule = ""
    brace_count = 0
    
    for char in css_text:
        current_rule += char
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                css_rules.append(current_rule.strip())
                current_rule = ""
    
    # Prioritize CSS rules by importance
    priority_rules = []
    normal_rules = []
    
    for rule in css_rules:
        rule_lower = rule.lower()
        # High priority: body, html, main layout elements, responsive styles
        if any(keyword in rule_lower for keyword in [
            'body', 'html', ':root', 'main', 'header', 'footer', 
            'nav', 'section', 'article', '@media', 'container',
            'grid', 'flex', 'layout', 'width', 'height', 'margin', 'padding'
        ]):
            priority_rules.append(rule)
        else:
            normal_rules.append(rule)
    
    # Combine rules until we hit the character limit
    result_css = ""
    
    # Add priority rules first
    for rule in priority_rules:
        if len(result_css) + len(rule) <= max_chars:
            result_css += rule + "\n"
        else:
            break
    
    # Add normal rules if space remains
    for rule in normal_rules:
        if len(result_css) + len(rule) <= max_chars:
            result_css += rule + "\n"
        else:
            break
    
    print(f"🎨 CSS truncated from {len(css_text)} to {len(result_css)} chars")
    return result_css

def extract_essential_meta(head_html: str) -> str:
    """
    Extract only essential meta tags from head to save tokens
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(head_html, 'html.parser')
    for a in soup.find_all("a"):
        a['href'] = '#'
    essential_tags = []
    
    # Keep essential meta tags
    for tag in soup.find_all(['title', 'meta']):
        if tag.name == 'title':
            essential_tags.append(str(tag))
        elif tag.name == 'meta':
            # Keep viewport, charset, and description
            attrs = tag.attrs
            if any(key in attrs for key in ['charset', 'name', 'property']):
                if attrs.get('name') in ['viewport', 'description'] or \
                   attrs.get('property') in ['og:title', 'og:description'] or \
                   'charset' in attrs:
                    essential_tags.append(str(tag))
    
    return '\n'.join(essential_tags)

def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (1 token ≈ 4 characters for most models)
    """
    return len(text) // 4

SYSTEM_PROMPT = """
You are an expert front-end engineer specializing in HTML/CSS replication.

Given the essential meta tags and the complete <body> HTML with CSS styles, produce a single, standalone HTML document that visually replicates the original website.

CRITICAL REQUIREMENTS:
- Include ALL content from the <body> section exactly as provided
- Preserve complete DOM structure with all nested elements
- Include essential meta tags (title, viewport, charset)
- Inline the provided CSS inside a <style> tag in the <head>
- Maintain all class names, IDs, and structural tags
- Keep all text content, links, and interactive elements
- Use minimal DOCTYPE declaration (<!DOCTYPE html>)
- Ensure the document is fully self-contained

STRUCTURE:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Original Title</title>
    <style>
        /* Provided CSS here */
    </style>
</head>
<body>
    <!-- Complete body content exactly as provided -->
</body>
</html>
```

Return ONLY the final HTML document with no commentary or explanations.
"""

async def generate_clone_html(design_ctx: Dict[str, str]) -> str:
    """
    Generate a full HTML clone without truncating CSS or body content.
    """

    print("🤖 Starting full-fidelity LLM HTML generation...")

    head_html = design_ctx.get("head", "")
    body_html = design_ctx.get("body", "")
    css_text = design_ctx.get("css", "")
    url = design_ctx.get("url", "Unknown")

    user_message = f"""
    SOURCE URL: {url}

    <HEAD_SECTION>
    {head_html}
    </HEAD_SECTION>

    <BODY_SECTION>
    {body_html}
    </BODY_SECTION>

    <STYLE_SHEET>
    {css_text}
    </STYLE_SHEET>

    Generate a complete standalone HTML document that includes:
    1. The full <head> section from HEAD_SECTION (including all meta tags and scripts)
    2. The complete <body> content from BODY_SECTION (preserve ALL nested elements)
    3. All CSS styles from STYLE_SHEET embedded in a <style> tag inside <head>

    IMPORTANT:
    - Do NOT truncate or modify any of the content.
    - Maintain full structure of <html>, <head>, and <body>.
    - Return ONLY the complete HTML document starting with <!DOCTYPE html>.
    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {"role": "user", "content": user_message.strip()}
    ]

    print("📤 Sending full content to LLM...")
    print(f"Final message length: {len(user_message)} characters")

    try:
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=MODEL_ID,
                messages=messages
            )
        )

        raw_response = response.choices[0].message.content.strip()
        print(f"📥 LLM Response length: {len(raw_response)} characters")

        # Return HTML directly if it starts with DOCTYPE
        html_start = raw_response.find("<!DOCTYPE html>")
        if html_start != -1:
            return raw_response[html_start:]
        else:
            print("⚠️ LLM output missing <!DOCTYPE html>. Returning full response.")
            return raw_response

    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        {head_html}
        <style>{css_text}</style>
        </head>
        {body_html}
        </html>
        """
