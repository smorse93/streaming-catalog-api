"""
Pydantic Models for API Request/Response Schemas
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class StreamingServiceEnum(str, Enum):
    NETFLIX = "netflix"
    PRIME = "prime"
    DISNEY = "disney"
    HBO = "hbo"
    PEACOCK = "peacock"
    APPLE = "apple"
    HULU = "hulu"


class ContentTypeEnum(str, Enum):
    MOVIE = "movie"
    SERIES = "series"


class StreamingOption(BaseModel):
    """Represents a streaming option for a title"""
    service: str = ""
    service_name: str = ""
    type: str = "unknown"  # subscription, rent, buy, free
    link: Optional[str] = None
    quality: Optional[str] = None
    price: Optional[Any] = None  # Can be dict, string, or None
    available_since: Optional[Union[str, int]] = None  # Can be timestamp int or string
    leaving_soon: Optional[bool] = None
    expiry_date: Optional[Union[str, int]] = None  # Can be timestamp int or string


class Title(BaseModel):
    """Represents a movie or TV series"""
    id: str = ""
    imdb_id: Optional[str] = None
    tmdb_id: Optional[str] = None
    title: str = "Unknown"
    type: str = "movie"  # movie or series
    year: Optional[int] = None
    overview: Optional[str] = None
    genres: List[str] = []
    imdb_rating: Optional[float] = Field(None, description="IMDB rating (0-10)")
    imdb_vote_count: Optional[int] = None
    runtime: Optional[int] = Field(None, description="Runtime in minutes")
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    directors: List[str] = []
    cast: List[str] = []
    streaming_options: List[StreamingOption] = []


class CatalogResponse(BaseModel):
    """Response for catalog endpoint"""
    service: str
    service_name: str
    country: str
    total_results: int
    page: int
    page_size: int
    has_more: bool
    titles: List[Title]


class MultiServiceCatalogResponse(BaseModel):
    """Response for multi-service catalog comparison"""
    country: str
    services: List[str]
    total_unique_titles: int
    titles: List[Title]


class ServiceComparisonResponse(BaseModel):
    """Response for service comparison"""
    country: str
    services: Dict[str, Dict[str, Any]]
    overlap_stats: Dict[str, Any]


class RatingRangeRequest(BaseModel):
    """Request body for filtering by IMDB rating range"""
    min_rating: Optional[float] = Field(None, ge=0, le=10)
    max_rating: Optional[float] = Field(None, ge=0, le=10)
    services: List[StreamingServiceEnum] = []
    content_type: Optional[ContentTypeEnum] = None
    genres: List[str] = []


class TopRatedResponse(BaseModel):
    """Response for top rated titles"""
    service: str
    country: str
    content_type: Optional[str]
    limit: int
    titles: List[Title]


class SearchRequest(BaseModel):
    """Request body for searching titles"""
    query: str
    services: List[StreamingServiceEnum] = []
    content_type: Optional[ContentTypeEnum] = None
    min_rating: Optional[float] = Field(None, ge=0, le=10)


class SearchResponse(BaseModel):
    """Response for search endpoint"""
    query: str
    total_results: int
    titles: List[Title]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    services_supported: List[str]


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    status_code: int
