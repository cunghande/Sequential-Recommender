"""Shim giu lenh cu `uvicorn backend.main:app` hoat dong."""

from backend.app.main import app

__all__ = ["app"]

