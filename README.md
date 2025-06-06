# Orchids SWE Intern Challenge - Parin Acharya
---

This project consists of a backend built with FastAPI and a frontend built with Next.js and TypeScript.

## Tools and technologies

| Category | Tool/Technology | Description |
|----------|----------------|-------------|
| **Frontend Framework** | Next.js | React framework for building server-side rendered and static web applications |
| **Frontend Language** | TypeScript | Typed superset of JavaScript for better development experience |
| **Frontend UI** | Tailwind CSS | Utility-first CSS framework for rapid UI development |
| **Frontend Components** | Radix UI, ShadcnUI | Unstyled, accessible components for building high‑quality design systems |
| **Backend Framework** | FastAPI | Modern, fast web framework for building APIs with Python |
| **Backend Language** | Python | Programming language used for backend development |
| **Package Management** | uv | Fast Python package installer and resolver |
| **API Integration** | Groq | AI model API integration |
| **API Integration** | Google Generative AI | Google's AI model integration |
| **Web Scraping** | Playwright | End-to-end testing and web scraping tool |
| **Template Engine** | Jinja2 | Template engine for Python |
| **Environment Variables** | python-dotenv | Package for loading environment variables |
| **HTTP Client** | httpx | Modern HTTP client for Python |
| **Data Validation** | Pydantic | Data validation and settings management using Python type annotations |
| **Web Server** | Uvicorn | ASGI server implementation for Python |

## Sample cloned websites

The following are examples of websites that have been cloned and modified:

### 1. Orchids Landing Page
- Original: [Orchids Landing Page](cloned_sites/cloned_orchids_landing_page.html)
- Modified: [Edited Orchids Landing Page](cloned_sites/edited_orchids_landing_page.html)

### 2. Apple Kenya
- [Apple Kenya Page](cloned_sites/cloned_apple_ke_page.html)

### 3. Amazon Shopping
- [Amazon Shopping Page](cloned_sites/cloned_amazon_shopping_page.html)

### 4. GitHub Sample
- [GitHub Sample Page](cloned_sites/cloned_sample_github_page.html)

Note: These are local HTML files that can be viewed by opening them in a web browser. The files are located in the `backend/app/cloned_sites` directory.

## Environment variables
Be sure to create a .env file in the backend folder containing:

```bash
HF_API_TOKEN=your_hugging_face_api_token
GROQ_API_KEY=your_groq_api_token
GOOGLE_API_KEY=your_google_api_token
UPSTASH_REDIS_REST_URL=your_upstash_redis_rest_token
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_rest_url

```

## Backend

The backend uses `uv` for package management.

### Installation

To install the backend dependencies, run the following command in the backend project directory:

```bash
uv sync
```

### Running the Backend

To run the backend development server, use the following command:

```bash
cd backend
py -3.11 -m venv venv311
.\venv311\Scripts\Activate.ps1 (In PowerShell)
pip install -r requirements.txt
playwright install chromium
```

Then input:
```bash

cd app
uvicorn main:app --reload
```

## Frontend

The frontend is built with Next.js and TypeScript.

### Installation

To install the frontend dependencies, navigate to the frontend project directory and run:

```bash
cd frontend
npm install
```

### Running the Frontend

To start the frontend development server, run:

```bash
npm run dev
```
