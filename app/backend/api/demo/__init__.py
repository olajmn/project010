"""
Public demo mode (docs/05-decisions.md #70, docs/demo.md): one
shared password, sessions, and limits in front of the API. Off unless
DEMO_MODE is set; then the API (backend/api/app.py) passes every
request through guard() first, by way of middleware.py.
"""

from backend.api.demo.check import guard
from backend.api.demo.settings import ENABLED, MAP_START_DEPTH, START_PROJECT

__all__ = ["ENABLED", "MAP_START_DEPTH", "START_PROJECT", "guard"]
