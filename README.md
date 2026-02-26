# Memora.Dev

Memora.Dev is an AI-powered organizational memory platform that solves institutional knowledge loss in software development teams. By observing code reviews, pull requests, and commits, it builds a **Decision Knowledge Graph** to trace the "why" behind your architecture using AI-driven inference.

## Features

- **Passive Knowledge Ingestion**: Automatically grabs changes and architectural discussions from GitHub via Webhooks.
- **Agentic Inference**: Dedicated AI agents parse rationale behind every architectural choice.
- **Decision Knowledge Graph**: Links intents, execution (code), authorities, and outcomes mapped over time.
- **Human Validation Mechanism**: Low-confidence insights get routed directly to team veterans for cross-review.
- **Semantic Querying**: Query natural language (e.g. "Why was the database abstracted?").

---

## Tech Stack

### Frontend Client (`/client`)
- **Framework**: Next.js 16 (React 19)
- **Styling**: Tailwind CSS
- **Components**: Radix UI / Shadcn

### Backend API (`/flask`)
- **Framework**: Python / Flask
- **Database**: PostgreSQL (SQLAlchemy & Alembic for Object-Relational Mapping / Migrations)
- **Security**: Flask-Bcrypt, Flask-JWT-Extended, Flask-CORS

---

## Local Development Setup

### 1. Requirements
Ensure you have the following installed on your machine:
- Node.js & npm (v20+)
- Python (v3.9+)
- PostgreSQL (or equivalent SQL database)

### 2. Setting up the Backend (Flask)

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd flask
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables by creating a `.env` file in the `flask` folder. *Note: Do not commit `.env` into source control. Keep your credentials safe.*
   ```env
   # .env example
   FLASK_APP=run.py
   FLASK_ENV=development
   DATABASE_URI=postgresql://<user>:<password>@<host>/<database>
   SECRET_KEY=your_super_secret_key
   JWT_SECRET_KEY=your_jwt_secret_key
   ```
5. Initialize the database schema and run the web server:
   ```bash
   python run.py
   ```

### 3. Setting up the Frontend (Next.js)

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd client
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Set up environment variables by creating a `.env.local` file in the `client` folder.
   ```env
   # .env.local example
   NEXT_PUBLIC_API_URL=http://localhost:5000
   ```
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```

### 4. Running the application
- Open your browser and navigate to `http://localhost:3000` to interact with the Memora.Dev frontend.
- The Flask API will typically be running on `http://localhost:5000`.

---

## Security Best Practices
- **Do not commit credentials**. Keep `.env` files secured locally and add them to `.gitignore`.
- Run migrations carefully before manipulating complex Knowledge Graph data.
- Enforce strict API keys when interacting directly with the GitHub Webhooks Integration system.
