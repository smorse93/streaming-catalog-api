"""
Streaming Catalog API with IMDB Ratings

A FastAPI backend that aggregates streaming service catalogs from
Netflix, Prime Video, Peacock, Disney+, Apple TV+, and HBO Max (Max),
and pairs them with IMDB ratings.

This API uses the Streaming Availability API via RapidAPI as its data source.
"""
import os
import logging
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Depends, Path
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .config import STREAMING_SERVICES, DEFAULT_COUNTRY, DEFAULT_PAGE_SIZE
from .models import (
    CatalogResponse,
    MultiServiceCatalogResponse,
    ServiceComparisonResponse,
    TopRatedResponse,
    SearchRequest,
    SearchResponse,
    HealthResponse,
    ErrorResponse,
    StreamingServiceEnum,
    ContentTypeEnum,
    Title
)
from .streaming_client import StreamingAPIClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize API client
api_client: Optional[StreamingAPIClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global api_client
    
    # Get API key from environment
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        logger.warning(
            "RAPIDAPI_KEY not set. API will run in demo mode with limited functionality. "
            "Get your free API key at: https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability"
        )
        api_key = "demo_key"  # Will fail on actual requests
    
    api_client = StreamingAPIClient(api_key)
    logger.info("Streaming Catalog API started")
    
    yield
    
    logger.info("Streaming Catalog API shutdown")


# Create FastAPI app
app = FastAPI(
    title="Streaming Catalog API with IMDB Ratings",
    description="""
    A comprehensive API that aggregates streaming service catalogs and pairs them with IMDB ratings.
    
    ## Supported Streaming Services
    - **Netflix** - `netflix`
    - **Amazon Prime Video** - `prime`
    - **Disney+** - `disney`
    - **Max (HBO Max)** - `hbo`
    - **Peacock** - `peacock`
    - **Apple TV+** - `apple`
    
    ## Features
    - Get full catalogs for each streaming service with IMDB ratings
    - Search for titles across all services
    - Compare catalogs between services
    - Filter by genre, year, rating, and content type
    - Get top-rated content for each service
    
    ## Data Source
    This API sources data from the Streaming Availability API, which aggregates
    streaming catalogs and IMDB ratings into a single data source.
    """,
    version="1.0.0",
    lifespan=lifespan,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client() -> StreamingAPIClient:
    """Dependency to get the API client."""
    if api_client is None:
        raise HTTPException(status_code=500, detail="API client not initialized")
    return api_client


# =============================================================================
# Health & Info Endpoints
# =============================================================================

@app.get("/", response_model=HealthResponse, tags=["Health"])
async def root():
    """Health check and API info."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services_supported=list(STREAMING_SERVICES.keys())
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services_supported=list(STREAMING_SERVICES.keys())
    )


@app.get("/services", tags=["Info"])
async def list_services():
    """List all supported streaming services."""
    return {
        "services": STREAMING_SERVICES,
        "total": len(STREAMING_SERVICES)
    }


# =============================================================================
# Catalog Endpoints
# =============================================================================

@app.get(
    "/catalog/{service}",
    response_model=CatalogResponse,
    tags=["Catalog"],
    summary="Get catalog for a streaming service"
)
async def get_service_catalog(
    service: StreamingServiceEnum = Path(..., description="Streaming service ID"),
    country: str = Query(DEFAULT_COUNTRY, description="Country code (e.g., us, gb, ca)"),
    content_type: Optional[ContentTypeEnum] = Query(None, description="Filter by content type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Results per page"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum IMDB rating"),
    max_rating: Optional[float] = Query(None, ge=0, le=10, description="Maximum IMDB rating"),
    genres: Optional[str] = Query(None, description="Comma-separated genre names"),
    order_by: str = Query("rating", description="Sort by: rating, year, title"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Get the complete catalog for a specific streaming service.
    
    Returns all movies and TV shows available on the service,
    paired with their IMDB ratings and other metadata.
    
    **Example:**
    ```
    GET /catalog/netflix?country=us&content_type=movie&min_rating=7.0
    ```
    """
    try:
        genre_list = genres.split(",") if genres else None
        
        result = await client.get_catalog_by_service(
            service=service.value,
            country=country,
            content_type=content_type.value if content_type else None,
            page=page,
            page_size=page_size,
            min_rating=min_rating,
            max_rating=max_rating,
            genres=genre_list,
            order_by=order_by
        )
        
        service_info = STREAMING_SERVICES.get(service.value, {})
        
        return CatalogResponse(
            service=service.value,
            service_name=service_info.get("name", service.value),
            country=country,
            total_results=result["total_results"],
            page=page,
            page_size=page_size,
            has_more=result["has_more"],
            titles=result["titles"]
        )
        
    except Exception as e:
        logger.error(f"Error fetching catalog for {service}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/catalog",
    response_model=MultiServiceCatalogResponse,
    tags=["Catalog"],
    summary="Get catalog from multiple services"
)
async def get_multi_service_catalog(
    services: str = Query(..., description="Comma-separated service IDs (e.g., netflix,prime,disney)"),
    country: str = Query(DEFAULT_COUNTRY, description="Country code"),
    content_type: Optional[ContentTypeEnum] = Query(None, description="Filter by content type"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum IMDB rating"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Get combined catalog from multiple streaming services.
    
    Returns unique titles available across the specified services,
    with information about which services each title is available on.
    
    **Example:**
    ```
    GET /catalog?services=netflix,prime,disney&min_rating=8.0
    ```
    """
    try:
        service_list = [s.strip() for s in services.split(",")]
        
        # Validate services
        valid_services = list(STREAMING_SERVICES.keys())
        invalid = [s for s in service_list if s not in valid_services]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid services: {invalid}. Valid options: {valid_services}"
            )
        
        result = await client.get_multi_service_catalog(
            services=service_list,
            country=country,
            content_type=content_type.value if content_type else None,
            min_rating=min_rating
        )
        
        return MultiServiceCatalogResponse(
            country=country,
            services=service_list,
            total_unique_titles=result["total_unique_titles"],
            titles=result["titles"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching multi-service catalog: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Top Rated Endpoints
# =============================================================================

@app.get(
    "/top-movies/{service}",
    response_model=TopRatedResponse,
    tags=["Top Rated"],
    summary="Get top X movies for a streaming service"
)
async def get_top_movies(
    service: StreamingServiceEnum = Path(..., description="Streaming service ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of top movies to return"),
    country: str = Query(DEFAULT_COUNTRY, description="Country code (e.g., us, gb, ca)"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum IMDB rating filter"),
    genre: Optional[str] = Query(None, description="Filter by genre (e.g., Action, Comedy, Drama)"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Get the top X highest-rated movies on a streaming service.
    
    Returns movies sorted by IMDB rating in descending order.
    
    **Examples:**
    ```
    GET /top-movies/netflix?limit=10
    GET /top-movies/prime?limit=25&min_rating=7.5
    GET /top-movies/disney?limit=20&genre=Animation
    GET /top-movies/hbo?limit=15&country=gb
    ```
    
    **Supported Services:**
    - `netflix` - Netflix
    - `prime` - Amazon Prime Video
    - `disney` - Disney+
    - `hbo` - Max (HBO Max)
    - `peacock` - Peacock
    - `apple` - Apple TV+
    """
    try:
        genre_list = [genre] if genre else None
        
        result = await client.get_catalog_by_service(
            service=service.value,
            country=country,
            content_type="movie",  # Always movies
            page_size=min(limit, 100),
            min_rating=min_rating,
            genres=genre_list,
            order_by="rating"
        )
        
        # Ensure we only return the requested number
        titles = result["titles"][:limit]
        
        return TopRatedResponse(
            service=service.value,
            country=country,
            content_type="movie",
            limit=limit,
            titles=titles
        )
        
    except Exception as e:
        logger.error(f"Error fetching top movies for {service}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/top-rated/{service}",
    response_model=TopRatedResponse,
    tags=["Top Rated"],
    summary="Get top rated titles for a service"
)
async def get_top_rated(
    service: StreamingServiceEnum = Path(..., description="Streaming service ID"),
    country: str = Query(DEFAULT_COUNTRY, description="Country code"),
    content_type: Optional[ContentTypeEnum] = Query(None, description="Filter by content type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Get the top rated movies and/or TV shows for a streaming service.
    
    Returns titles sorted by IMDB rating in descending order.
    
    **Example:**
    ```
    GET /top-rated/netflix?content_type=movie&limit=25
    ```
    """
    try:
        titles = await client.get_top_rated(
            service=service.value,
            country=country,
            content_type=content_type.value if content_type else None,
            limit=limit
        )
        
        return TopRatedResponse(
            service=service.value,
            country=country,
            content_type=content_type.value if content_type else None,
            limit=limit,
            titles=titles
        )
        
    except Exception as e:
        logger.error(f"Error fetching top rated for {service}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/top-movies",
    tags=["Top Rated"],
    summary="Get top movies across all streaming services"
)
async def get_top_movies_all_services(
    limit: int = Query(10, ge=1, le=25, description="Number of top movies per service"),
    country: str = Query(DEFAULT_COUNTRY, description="Country code"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum IMDB rating"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Get top movies from ALL streaming services in one call.
    
    Returns the top X movies for each service (Netflix, Prime, Disney+, HBO Max, Peacock, Apple TV+).
    
    **Example:**
    ```
    GET /top-movies?limit=10&min_rating=7.0
    ```
    
    **Response includes top movies from:**
    - Netflix
    - Amazon Prime Video  
    - Disney+
    - Max (HBO Max)
    - Peacock
    - Apple TV+
    """
    try:
        results = {}
        
        for service_id, service_info in STREAMING_SERVICES.items():
            try:
                result = await client.get_catalog_by_service(
                    service=service_id,
                    country=country,
                    content_type="movie",
                    page_size=limit,
                    min_rating=min_rating,
                    order_by="rating"
                )
                
                titles = result["titles"][:limit]
                results[service_id] = {
                    "service_name": service_info["name"],
                    "movie_count": len(titles),
                    "movies": [t.model_dump() for t in titles]
                }
            except Exception as e:
                logger.warning(f"Error fetching top movies for {service_id}: {e}")
                results[service_id] = {
                    "service_name": service_info["name"],
                    "error": str(e),
                    "movies": []
                }
        
        return {
            "country": country,
            "limit_per_service": limit,
            "min_rating": min_rating,
            "services": results
        }
        
    except Exception as e:
        logger.error(f"Error fetching top movies across services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/top-rated",
    tags=["Top Rated"],
    summary="Get top rated titles across all services"
)
async def get_top_rated_all_services(
    country: str = Query(DEFAULT_COUNTRY, description="Country code"),
    content_type: Optional[ContentTypeEnum] = Query(None, description="Filter by content type"),
    limit: int = Query(10, ge=1, le=50, description="Number of titles per service"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Get top rated titles from all supported streaming services.
    
    Returns top titles for each service in a single response.
    """
    try:
        results = {}
        
        for service_id in STREAMING_SERVICES.keys():
            try:
                titles = await client.get_top_rated(
                    service=service_id,
                    country=country,
                    content_type=content_type.value if content_type else None,
                    limit=limit
                )
                results[service_id] = {
                    "service_name": STREAMING_SERVICES[service_id]["name"],
                    "titles": [t.model_dump() for t in titles]
                }
            except Exception as e:
                logger.warning(f"Error fetching top rated for {service_id}: {e}")
                results[service_id] = {"error": str(e), "titles": []}
        
        return {
            "country": country,
            "content_type": content_type.value if content_type else "all",
            "limit_per_service": limit,
            "services": results
        }
        
    except Exception as e:
        logger.error(f"Error fetching top rated across services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Search Endpoints
# =============================================================================

@app.get(
    "/search",
    response_model=SearchResponse,
    tags=["Search"],
    summary="Search for titles by name"
)
async def search_titles(
    q: str = Query(..., min_length=1, description="Search query"),
    country: str = Query(DEFAULT_COUNTRY, description="Country code"),
    services: Optional[str] = Query(None, description="Comma-separated service IDs to search"),
    content_type: Optional[ContentTypeEnum] = Query(None, description="Filter by content type"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Search for movies and TV shows by title.
    
    Returns matching titles with their streaming availability and IMDB ratings.
    
    **Example:**
    ```
    GET /search?q=inception&services=netflix,prime
    ```
    """
    try:
        service_list = None
        if services:
            service_list = [s.strip() for s in services.split(",")]
        
        titles = await client.search_titles(
            query=q,
            country=country,
            services=service_list,
            content_type=content_type.value if content_type else None
        )
        
        return SearchResponse(
            query=q,
            total_results=len(titles),
            titles=titles
        )
        
    except Exception as e:
        logger.error(f"Error searching titles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/search",
    response_model=SearchResponse,
    tags=["Search"],
    summary="Advanced search with filters"
)
async def advanced_search(
    request: SearchRequest,
    country: str = Query(DEFAULT_COUNTRY, description="Country code"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Advanced search with additional filters.
    
    Allows searching with minimum rating filter and multiple service selection.
    """
    try:
        service_list = [s.value for s in request.services] if request.services else None
        
        titles = await client.search_titles(
            query=request.query,
            country=country,
            services=service_list,
            content_type=request.content_type.value if request.content_type else None
        )
        
        # Apply rating filter if specified
        if request.min_rating is not None:
            titles = [t for t in titles if t.imdb_rating and t.imdb_rating >= request.min_rating]
        
        return SearchResponse(
            query=request.query,
            total_results=len(titles),
            titles=titles
        )
        
    except Exception as e:
        logger.error(f"Error in advanced search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Title Lookup Endpoints
# =============================================================================

@app.get(
    "/title/imdb/{imdb_id}",
    response_model=Title,
    tags=["Title Lookup"],
    summary="Get title by IMDB ID"
)
async def get_title_by_imdb(
    imdb_id: str = Path(..., description="IMDB ID (e.g., tt0111161)"),
    country: str = Query(DEFAULT_COUNTRY, description="Country code for streaming availability"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Look up a specific movie or TV show by its IMDB ID.
    
    Returns full details including streaming availability across all services
    and IMDB rating information.
    
    **Example:**
    ```
    GET /title/imdb/tt0111161  # The Shawshank Redemption
    ```
    """
    try:
        title = await client.get_title_by_imdb_id(imdb_id, country)
        
        if title is None:
            raise HTTPException(status_code=404, detail=f"Title not found: {imdb_id}")
        
        return title
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching title {imdb_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Comparison Endpoints
# =============================================================================

@app.get(
    "/compare",
    response_model=ServiceComparisonResponse,
    tags=["Comparison"],
    summary="Compare streaming service catalogs"
)
async def compare_services(
    services: str = Query(..., description="Comma-separated service IDs to compare"),
    country: str = Query(DEFAULT_COUNTRY, description="Country code"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Compare catalogs between multiple streaming services.
    
    Returns statistics about each service's catalog including:
    - Total number of titles
    - Average IMDB rating
    - Number of movies vs series
    - Overlap with other services
    
    **Example:**
    ```
    GET /compare?services=netflix,prime,disney
    ```
    """
    try:
        service_list = [s.strip() for s in services.split(",")]
        
        # Validate services
        valid_services = list(STREAMING_SERVICES.keys())
        invalid = [s for s in service_list if s not in valid_services]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid services: {invalid}. Valid options: {valid_services}"
            )
        
        if len(service_list) < 2:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least 2 services to compare"
            )
        
        result = await client.compare_services(service_list, country)
        
        return ServiceComparisonResponse(
            country=country,
            services=result["services"],
            overlap_stats=result["overlap_stats"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Statistics Endpoints
# =============================================================================

@app.get(
    "/stats/{service}",
    tags=["Statistics"],
    summary="Get statistics for a streaming service"
)
async def get_service_stats(
    service: StreamingServiceEnum = Path(..., description="Streaming service ID"),
    country: str = Query(DEFAULT_COUNTRY, description="Country code"),
    client: StreamingAPIClient = Depends(get_client)
):
    """
    Get detailed statistics for a streaming service's catalog.
    
    Returns:
    - Total titles, movies, and series counts
    - Rating distribution
    - Top genres
    - Average IMDB rating
    """
    try:
        result = await client.get_catalog_by_service(
            service=service.value,
            country=country,
            page_size=100
        )
        
        titles = result["titles"]
        
        # Calculate statistics
        movies = [t for t in titles if t.type == "movie"]
        series = [t for t in titles if t.type == "series"]
        
        ratings = [t.imdb_rating for t in titles if t.imdb_rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Genre distribution
        genre_counts = {}
        for title in titles:
            for genre in title.genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Rating distribution
        rating_dist = {
            "9-10": len([r for r in ratings if r >= 9]),
            "8-9": len([r for r in ratings if 8 <= r < 9]),
            "7-8": len([r for r in ratings if 7 <= r < 8]),
            "6-7": len([r for r in ratings if 6 <= r < 7]),
            "below_6": len([r for r in ratings if r < 6])
        }
        
        return {
            "service": service.value,
            "service_name": STREAMING_SERVICES[service.value]["name"],
            "country": country,
            "statistics": {
                "total_titles": len(titles),
                "total_movies": len(movies),
                "total_series": len(series),
                "average_imdb_rating": round(avg_rating, 2),
                "highest_rated": max(ratings) if ratings else None,
                "lowest_rated": min(ratings) if ratings else None,
                "rating_distribution": rating_dist,
                "top_genres": dict(top_genres)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats for {service}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Run Application
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
