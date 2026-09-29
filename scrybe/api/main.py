"""Scrybe FastAPI Application.

Provides REST endpoints for triggering pipeline runs,
retrieving reports, and querying the pricing matrix.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from scrybe.api.routes import router
from scrybe.logging_config import setup_logging

setup_logging(settings.log_level)

app = FastAPI(
    title="Scrybe API",
    description=(
        "Scrybe — Autonomous Multi-Agent Web Intelligence System. "
        "Scrape, extract, validate, analyze, and generate cited market intelligence reports."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for Streamlit / frontend consumers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "scrybe-api",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
