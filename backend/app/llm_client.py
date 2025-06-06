# LLM + prompt template for the website cloner with CSS optimization

import os, re
import asyncio
from typing import Dict, Any, Literal
from dotenv import load_dotenv
import json
from groq import Groq
import logging
import google.generativeai as genai
from bs4 import BeautifulSoup

load_dotenv() 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

class LLMProvider:
    GROQ = "groq"
    GOOGLE = "google"

def get_model_config(model_id: str) -> tuple[str, str]:
    """
    Returns (provider, model_name) for the given model_id
    """
    model_map = {
        'llama-3.3-70b-versatile': (LLMProvider.GROQ, 'llama-3.3-70b-versatile'),
        'gemini-2.5-pro-preview-05-06': (LLMProvider.GOOGLE, 'gemini-2.5-pro-preview-05-06'),
        'mixtral-8x7b-32768': (LLMProvider.GROQ, 'mixtral-8x7b-32768')
    }
    config = model_map.get(model_id)
    if config is None:
         logger.error(f"Unknown model ID: {model_id}. Valid models are: {list(model_map.keys())}")
         raise ValueError(f"Unsupported model ID: {model_id}")

    return config

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

SYSTEM_PROMPT_CLONE = """
You are an expert front-end engineer specializing in HTML/CSS replication.

Given the following website context, produce a single, standalone HTML document that visually replicates the original website.

CONTEXT:

Head content:
{head_content}

Body content:
{body_content}

CSS:
{css_content}

CRITICAL REQUIREMENTS:
- Generate valid HTML5, fully self-contained.
- Include relevant content from the CONTEXT sections.
- Preserve key structural elements, class names, and IDs from the body content.
- Inline the provided CSS (if any) inside a <style> tag in the <head>.
- Ensure the document is responsive.
- Keep text content, links, and interactive elements.
- Use minimal DOCTYPE declaration (<!DOCTYPE html>).
- Do NOT include any external stylesheets or scripts unless explicitly necessary and inlined.
- Return ONLY the final HTML document with no commentary or explanations outside the ```html``` block.

STRUCTURE:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Original Title</title> {/* Placeholder, ideally get from head */}
    <style>
        /* Provided CSS here (if any) */
    </style>
    <!-- Other essential meta tags from context -->
</head>
<body>
    <!-- Replicated body content -->
</body>
</html>
```

Return ONLY the HTML code block, starting with ```html and ending with ```.
"""

# Define a separate system prompt for editing
SYSTEM_PROMPT_EDIT = """
You are an expert front-end engineer who can perform precise edits on HTML code based on user instructions.

Given the following HTML content and a specific editing instruction, produce the *full, modified* HTML document.

INPUT HTML:
```html
{html_content}
```

EDITING INSTRUCTION:
{instruction}

CRITICAL REQUIREMENTS:
- Apply the editing instruction accurately to the provided HTML.
- Maintain the overall structure and integrity of the original HTML.
- Ensure the output is valid, standalone HTML5.
- Include all original parts of the HTML except those modified by the instruction.
- Preserve existing inline styles and script tags unless the instruction explicitly requires modifying them.
- Do NOT add any extra commentary, explanations, or markdown formatting outside the ```html``` block.
- Return ONLY the full, edited HTML code block.

Return ONLY the HTML code block, starting with ```html and ending with ```.
"""

def create_prompt_clone(design_context: dict) -> str:
    """Create a standardized prompt for cloning based on design context."""
    head_content = design_context.get('head', '').strip()
    body_content = design_context.get('body', '').strip()
    css_content = design_context.get('css', '').strip()

    processed_head = head_content if head_content else "<title>Cloned Page</title>" # Ensure at least a title

    css_section_prompt = f"""
CSS:
{css_content}
    """ if css_content else "No specific CSS provided, use general styling principles for a clean, modern look."


    return f"""
    You are an expert front-end engineer specializing in HTML/CSS replication.

    Given the following website context, produce a single, standalone HTML document that visually replicates the original website.

    CONTEXT:

    Head content:
    {processed_head}

    Body content:
    {body_content}

    {css_section_prompt}

    CRITICAL REQUIREMENTS:
    - Generate valid HTML5, fully self-contained.
    - Include relevant content from the CONTEXT sections.
    - Preserve key structural elements, class names, and IDs from the body content.
    - Inline the provided CSS (if any) inside a <style> tag in the <head>.
    - Ensure the document is responsive.
    - Keep text content, links, and interactive elements.
    - Use minimal DOCTYPE declaration (<!DOCTYPE html>).
    - Do NOT include any external stylesheets or scripts unless explicitly necessary and inlined.
    - Return ONLY the final HTML document with no commentary or explanations outside the ```html``` block.

    STRUCTURE:
    ```html
    <!DOCTYPE html>
    <html>
    <head>
        {processed_head}
        <style>
            /* Provided CSS here (if any) */
        </style>
        <!-- Ensure essential meta tags like charset and viewport are present if not in provided head -->
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        {body_content}
    </body>
    </html>
    ```

    Return ONLY the HTML code block, starting with ```html and ending with ```.
    """

def create_prompt_edit(html_content: str, instruction: str) -> str:
    """Create a prompt for editing HTML."""
    return SYSTEM_PROMPT_EDIT.format(html_content=html_content, instruction=instruction)

async def generate_clone_html(design_context: dict, model_id: str) -> str:
    """
    Generate cloned HTML using the specified LLM (Groq or Google).
    """
    provider, model_name = get_model_config(model_id)
    logger.info(f"Using {provider} provider with model {model_name}")

    try:
        if provider == LLMProvider.GOOGLE:
            return await generate_with_google(model_name, create_prompt_clone(design_context))
        elif provider == LLMProvider.GROQ:
            return await generate_with_groq(model_name, create_prompt_clone(design_context))
    except Exception as e:
        logger.error(f"Error generating HTML with {provider}: {str(e)}")
        raise

async def generate_with_google(model_name: str, prompt: str) -> str:
    """Generate HTML using Google's Gemini model"""
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        return response.text
    except Exception as e:
        logger.error(f"Google AI generation error: {str(e)}")
        raise

async def generate_with_groq(model_name: str, prompt: str) -> str:
    """Generate HTML using Groq's models"""
    try:
        response = await groq_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        html_match = re.search(r'```html\n(.*?)\n```', content, re.DOTALL)
        if html_match:
            return html_match.group(1).strip()
        else:
            logger.warning(f"Groq response for model {model_name} did not contain an HTML code block. Returning full response. Content snippet: {content[:200]}...")
            return content.strip()

    except Exception as e:
        logger.error(f"Groq generation error: {str(e)}")
        raise

# --- New function for HTML Editing ---
async def edit_html_with_gemini(html_content: str, instruction: str, model_id: str = 'gemini-2.5-pro-preview-05-06') -> str:
    """
    Edit HTML content using a specified Gemini model.
    """
    provider, model_name = get_model_config(model_id)
    if provider != LLMProvider.GOOGLE:
        raise ValueError(f"Model {model_id} is not a supported Google model for editing.")

    logger.info(f"Editing HTML using Gemini model: {model_name}")

    try:
        prompt = create_prompt_edit(html_content, instruction)
        edited_html = await generate_with_google(model_name, prompt)

        html_match = re.search(r'```html\n(.*?)\n```', edited_html, re.DOTALL)
        if html_match:
            return html_match.group(1).strip()
        else:
            logger.warning("Gemini response for editing did not contain an HTML code block. Returning full response.")
            return edited_html.strip()

    except Exception as e:
        logger.error(f"Error editing HTML with Gemini model {model_id}: {str(e)}")
        raise
