# Orchids SWE Intern Challenge Template

This project consists of a backend built with FastAPI and a frontend built with Next.js and TypeScript.

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
source .\.venv311\Scripts\Activate
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
