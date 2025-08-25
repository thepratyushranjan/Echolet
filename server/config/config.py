# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings loaded from environment variables."""

    POSTGRES_CONNECTION = os.getenv("POSTGRES_CONNECTION")
    POSTGRES_MIGRATION = os.getenv("POSTGRES_MIGRATION")