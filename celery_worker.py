#!/usr/bin/env python3
"""
Celery Worker Entry Point
Chạy: python celery_worker.py hoặc celery -A celery_worker worker --loglevel=info
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.services.background_service import celery_app

if __name__ == "__main__":
    celery_app.start()