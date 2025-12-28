"""
Streaming Catalog API Package

A FastAPI backend that aggregates streaming service catalogs
and pairs them with IMDB ratings.
"""
from .main import app
from .streaming_client import StreamingAPIClient
from .models import Title, CatalogResponse, StreamingOption
from .config import STREAMING_SERVICES

__version__ = "1.0.0"
__all__ = [
    "app",
    "StreamingAPIClient", 
    "Title",
    "CatalogResponse",
    "StreamingOption",
    "STREAMING_SERVICES"
]
