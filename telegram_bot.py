#!/usr/bin/env python3
"""
Telegram Bot Entry Point
Chạy: python telegram_bot.py
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.integrations.telegram.runner import main

if __name__ == "__main__":
    main()