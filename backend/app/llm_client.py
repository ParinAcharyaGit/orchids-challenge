# LLM + prompt template for the website cloner
# using Llama 2 via HF Inference API

import os
import asyncio
from typing import Dict, Any
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import json


load_dotenv() 

HF_TOKEN = os.getenv("HF_API_TOKEN", None)
if not HF_TOKEN:
    raise RuntimeError("Missing HuggingFace Token")

inference_client = InferenceClient(
    token=HF_TOKEN
)

MODEL_ID = "meta-llama/Llama-2-13b"

SYSTEM_PROMPT = """
You are an expert front-end engineer. 
Given the complete <head> HTML, the fully rendered <body> HTML (with all <img> tags now inlined as Base64), 
and the critical CSS (only the CSS rules actually applied on this page during initial render), 
produce a single, standalone HTML document that visually replicates the original website as closely as possible.

Requirements:
- Include <meta> tags and <title> exactly as in the original <head>.
- Inline the critical CSS inside a <style> tag in the final <head>.
- Preserve all class names, IDs, and structural tags so that any additional CSS (if needed) still applies.
- Ensure every image (already Base64 in the <body>) displays correctly.
- Do not introduce any external references; the final document must be fully self-contained.
- Use a minimal DOCTYPE declaration (<!DOCTYPE html>) at the very top.
- Keep the original page’s language (<html lang="…">), if specified.

If you believe some CSS rules are missing, you can re-derive them from context, but preserve exactly as much as you have been given before making changes.

Return only the final HTML (no commentary, no markdown fences).
"""

async def generate_clone_html(design_ctx: Dict[str, str]) -> str:
    """
    design_ctx: {
      "head": "<head>…</head>",
      "body": "<body>…</body>",
      "css": "...critical CSS..."
    }

    We assemble a chat‐style payload with a system message + user message,
    then call Hugging Face’s Inference API (Llama 2 chat endpoint).
    """

    user_message = f"""
    <ORIGINAL_HEAD>
    {design_ctx['head']}
    </ORIGINAL_HEAD>

    <CURRENT_BODY>
    {design_ctx['body']}
    </CURRENT_BODY>

    <CRITICAL_CSS>
    {design_ctx['css']}
    </CRITICAL_CSS>

    Generate a complete, standalone HTML document that, when opened in a browser, renders identically
    to the original website. Include critical CSS in the <head> so that no external CSS files are needed.
    """

    prompt = f"{SYSTEM_PROMPT.strip()}\n\n{user_message.strip()}"

    try:
        response = inference_client.text_generation(
            prompt,
            model=MODEL_ID,
            max_new_tokens=1024
        )
    except Exception as e:
        # Log and raise or return a friendly error
        print("Error calling HF Inference API:", e)
        raise RuntimeError("Failed to generate response from model") from e
    
    print("Raw HF response:", response)

    # Handle standard response format
    # If response is string, try parse JSON safely
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            # Not JSON: raw error or HTML page returned
            print("Raw response (not JSON):", response)
            raise RuntimeError("Received non-JSON response from inference API")

    # Now handle expected response formats
    if isinstance(response, dict):
        if "generated_text" in response:
            return response["generated_text"].strip()
        if "choices" in response and isinstance(response["choices"], list):
            first = response["choices"][0]
            if "message" in first and "content" in first["message"]:
                return first["message"]["content"].strip()
            
    # The HF chat response will come back as a dict that—depending on the InferenceClient version—
    # often looks like: {"generated_text": "<assistant>…final html…"}
    # or {"choices": [{"message": {"content": "…html…"}}], …}
    #
    # We inspect common patterns:
    # if isinstance(response, dict) and 'generated_text' in response:
    #     # Case A: response has "choices" list → pick first choice’s message.content
    #     if "choices" in response and isinstance(response["choices"], list):
    #         first = response["choices"][0]
    #         if "message" in first and "content" in first["message"]:
    #             return first["message"]["content"].strip()
    #         # fallback to generated_text if present
    #     if "generated_text" in response:
    #         # Usually has the entire assistant reply
    #         return response["generated_text"].strip()

    # If the shape is different, attempt a naive str(response)
    return str(response).strip()


        
    