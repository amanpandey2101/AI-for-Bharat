from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import auth_router
from app.database import engine, Base

import logging

logger = logging.getLogger(__name__)

# Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI for Bharat - FastAPI Migration")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")

@app.get("/")
def read_root():
    return {"message": "Welcome to AI for Bharat FastAPI Backend"}
