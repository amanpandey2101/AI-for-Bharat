# AI-for-Bharat Backend (FastAPI)

This is the FastAPI migration of the original Flask backend. It provides authentication, GitHub OAuth, and user management services.

## 🚀 Quick Start

### 1. Setup Environment
Ensure you have a `.env` file in the `fastapi` root directory. Use the existing one or refer to the configuration in `app/config.py`.

### 2. Install Dependencies
```bash
# Create a virtual environment
python -m venv venv

# Activate it
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Run the Server
```bash
python run.py
```
The server will start at `http://127.0.0.1:5000` with hot-reloading enabled.

## 🛠 Tech Stack
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
- **Validation:** [Pydantic v2](https://docs.pydantic.dev/)
- **Auth:** JWT (stored in HttpOnly Cookies), Bcrypt
- **OAuth:** GitHub OAuth Integration

## 🗄 Database & Migrations

We use Alembic to manage database schema changes.

- **Generate a new migration:**
  ```bash
  alembic revision --autogenerate -m "description_of_changes"
  ```
- **Apply migrations:**
  ```bash
  alembic upgrade head
  ```
- **Revert last migration:**
  ```bash
  alembic downgrade -1
  ```

## 📂 Project Structure
```text
fastapi/
├── app/
│   ├── auth/          # Authentication routes (Login, Register, OAuth)
│   ├── core/          # Core configurations
│   ├── models/        # SQLAlchemy Database models
│   ├── utils/         # Helper functions (Security, Email, Dependencies)
│   ├── validators/    # Pydantic schemas for request validation
│   ├── config.py      # Pydantic Settings management
│   ├── database.py    # SQLAlchemy engine and session setup
├── migrations/        # Alembic migration scripts
├── main.py            # FastAPI app initialization
├── run.py             # Uvicorn runner script
└── requirements.txt   # Project dependencies
```

## API Documentation
Once the server is running, you can access the interactive API docs at:
- Swagger UI: [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs)
- ReDoc: [http://127.0.0.1:5000/redoc](http://127.0.0.1:5000/redoc)
