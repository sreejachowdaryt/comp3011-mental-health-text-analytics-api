"""
conftest.py — shared pytest configuration
Place this file in the root of your project (same level as /app and /tests)
"""

import os
import pytest

# Set test environment variables BEFORE any app imports
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")