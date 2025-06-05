# this is the file that handles changes requested by the user chat interface

import os
import asyncio
from typing import Dict
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("Missing Google API Key")

genai.configure(api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT = """
You are an expert HTML editor. Your task is to modify the provided HTML/CSS based on the user's instructions.
Follow these guidelines:
1. Make only the requested changes
2. Preserve the overall structure and functionality
3. Keep all other existing classes, IDs, and attributes the same
4. Return the complete HTML document
5. Ensure the HTML remains valid and well-formed
6. Do not add any explanatory text, just return the modified HTML

The response should start with <!DOCTYPE html> and contain the complete HTML document.
"""

async def edit_html(instruction: str, current_html: str) -> Dict[str, str]:
    """
    Edit HTML using Gemini 2.5 Pro model
    """
    model = genai.GenerativeModel("gemini-2.5-pro-preview-05-06")
    
    user_message = f"""
    CURRENT HTML:
    {current_html}

    INSTRUCTION:
    {instruction}

    Please modify the HTML according to the instruction. Return only the complete HTML document.
    """

    try:
        response = await asyncio.to_thread(
            lambda: model.generate_content(user_message)
        )
        
        modified_html = response.text.strip()
        
        # Ensure the response starts with DOCTYPE
        if not modified_html.startswith("<!DOCTYPE html>"):
            raise ValueError("Invalid HTML response from model")
            
        # Save the modified HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backend/app/cloned_sites/{timestamp}_edited.html"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(modified_html)
            
        return {
            "message": f"HTML has been updated and saved as {filename}",
            "html": modified_html
        }
        
    except Exception as e:
        raise Exception(f"Error editing HTML: {str(e)}")

