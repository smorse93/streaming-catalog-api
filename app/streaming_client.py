"""
Streaming Availability API Client Service

This module handles all interactions with the Streaming Availability API
via RapidAPI. It provides methods to fetch streaming catalogs and
match them with IMDB ratings.
"""
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from cachetools import TTLCache
import logging
from datetime import datetime

from .config import (
    STREAMING_SERVICES, 
    SERVICE_API_IDS, 
    DEFAULT_COUNTRY,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE
)
from .models import Title, StreamingOption

logger = logging.getLogger(__name__)

# Cache for API responses (1 hour TTL, max 1000 items)
_cache = TTLCache(maxsize=1000, ttl=3600)


class StreamingAPIClient:
    """
    Client for the Streaming Availability API.
    
    This API provides streaming availability data for movies and TV shows
    across multiple streaming platforms, including IMDB ratings.
    """
    
    BASE_URL = "https://streaming-availability.p.rapidapi.com"
    
    def __init__(self, api_key: str):
        """
        Initialize the API client.
        
        Args:
            api_key: RapidAPI key for the Streaming Availability API
        """
        self.api_key = api_key
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com"
        }
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Make an async HTTP request to the API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            use_cache: Whether to use cached responses
            
        Returns:
            JSON response from the API
        """
        url = f"{self.BASE_URL}/{endpoint}"
        cache_key = f"{endpoint}:{str(sorted(params.items()) if params else '')}"
        
        # Check cache first
        if use_cache and cache_key in _cache:
            logger.debug(f"Cache hit for {cache_key}")
            return _cache[cache_key]
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, 
                    headers=self.headers, 
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Cache the response
                if use_cache:
                    _cache[cache_key] = data
                
                return data
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error: {str(e)}")
                raise
    
    def _parse_title(self, show_data: Dict[str, Any], country: str = DEFAULT_COUNTRY) -> Title:
        """
        Parse API show data into a Title model.
        
        Args:
            show_data: Raw show data from the API
            country: Country code for streaming options
            
        Returns:
            Parsed Title object
        """
        # Extract streaming options for the specified country
        streaming_options = []
        streaming_info = show_data.get("streamingOptions", {}).get(country, [])
        
        for option in streaming_info:
            service_id = option.get("service", {}).get("id", "")
            streaming_options.append(StreamingOption(
                service=service_id,
                service_name=option.get("service", {}).get("name", service_id),
                type=option.get("type", "unknown"),
                link=option.get("link"),
                quality=option.get("quality"),
                price=option.get("price"),
                available_since=option.get("availableSince"),
                leaving_soon=option.get("leavingSoon"),
                expiry_date=option.get("expiringDate")
            ))
        
        # Extract genres
        genres = [g.get("name", "") for g in show_data.get("genres", [])]
        
        # Extract cast
        cast = [c.get("name", "") for c in show_data.get("cast", [])][:10]  # Limit to top 10
        
        # Extract directors
        directors = [d.get("name", "") for d in show_data.get("directors", [])]
        
        # Get poster and backdrop URLs
        poster_url = None
        backdrop_url = None
        image_set = show_data.get("imageSet", {})
        if image_set:
            poster_url = image_set.get("verticalPoster", {}).get("w480")
            backdrop_url = image_set.get("horizontalBackdrop", {}).get("w720")
        
        return Title(
            id=show_data.get("id", ""),
            imdb_id=show_data.get("imdbId"),
            tmdb_id=str(show_data.get("tmdbId", "")) if show_data.get("tmdbId") else None,
            title=show_data.get("title", "Unknown"),
            type=show_data.get("showType", "movie"),
            year=show_data.get("releaseYear") or show_data.get("firstAirYear"),
            overview=show_data.get("overview"),
            genres=genres,
            imdb_rating=show_data.get("rating"),  # API provides IMDB rating directly
            imdb_vote_count=show_data.get("ratingCount"),
            runtime=show_data.get("runtime"),
            poster_url=poster_url,
            backdrop_url=backdrop_url,
            directors=directors,
            cast=cast,
            streaming_options=streaming_options
        )
    
    async def get_catalog_by_service(
        self,
        service: str,
        country: str = DEFAULT_COUNTRY,
        content_type: Optional[str] = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        genres: Optional[List[str]] = None,
        order_by: str = "rating"
    ) -> Dict[str, Any]:
        """
        Get the catalog for a specific streaming service.
        
        Args:
            service: Service ID (netflix, prime, disney, hbo, peacock, apple)
            country: Country code (default: us)
            content_type: Filter by type (movie or series)
            page: Page number for pagination
            page_size: Number of results per page
            min_rating: Minimum IMDB rating filter
            max_rating: Maximum IMDB rating filter
            genres: List of genre names to filter by
            order_by: Sort order (rating, year, title)
            
        Returns:
            Dictionary with catalog data and pagination info
        """
        service_id = SERVICE_API_IDS.get(service, service)
        
        params = {
            "country": country,
            "catalogs": service_id,
            "order_by": order_by,
            "order_direction": "desc" if order_by == "rating" else "asc"
        }
        
        if content_type:
            params["show_type"] = content_type
        
        if min_rating is not None:
            params["rating_min"] = int(min_rating * 10)  # API uses 0-100 scale
        
        if max_rating is not None:
            params["rating_max"] = int(max_rating * 10)
        
        if genres:
            params["genres"] = ",".join(genres)
        
        # Handle pagination with cursor
        params["output_language"] = "en"
        
        try:
            data = await self._make_request("shows/search/filters", params)
            
            shows = data.get("shows", [])
            titles = [self._parse_title(show, country) for show in shows]
            
            # Calculate pagination
            has_more = data.get("hasMore", False)
            
            return {
                "titles": titles,
                "total_results": len(titles),
                "page": page,
                "page_size": page_size,
                "has_more": has_more,
                "cursor": data.get("nextCursor")
            }
            
        except Exception as e:
            logger.error(f"Error fetching catalog for {service}: {str(e)}")
            raise
    
    async def get_title_by_imdb_id(
        self, 
        imdb_id: str, 
        country: str = DEFAULT_COUNTRY
    ) -> Optional[Title]:
        """
        Get a specific title by IMDB ID.
        
        Args:
            imdb_id: IMDB ID (e.g., tt0111161)
            country: Country code for streaming availability
            
        Returns:
            Title object or None if not found
        """
        params = {"country": country}
        
        try:
            data = await self._make_request(f"shows/{imdb_id}", params)
            return self._parse_title(data, country)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def search_titles(
        self,
        query: str,
        country: str = DEFAULT_COUNTRY,
        services: Optional[List[str]] = None,
        content_type: Optional[str] = None
    ) -> List[Title]:
        """
        Search for titles by name.
        
        Args:
            query: Search query string
            country: Country code
            services: List of service IDs to filter by
            content_type: Filter by type (movie or series)
            
        Returns:
            List of matching Title objects
        """
        params = {
            "country": country,
            "title": query,
            "output_language": "en"
        }
        
        if content_type:
            params["show_type"] = content_type
        
        if services:
            service_ids = [SERVICE_API_IDS.get(s, s) for s in services]
            params["catalogs"] = ",".join(service_ids)
        
        try:
            data = await self._make_request("shows/search/title", params)
            shows = data if isinstance(data, list) else data.get("shows", [])
            return [self._parse_title(show, country) for show in shows]
        except Exception as e:
            logger.error(f"Error searching titles: {str(e)}")
            raise
    
    async def get_top_rated(
        self,
        service: str,
        country: str = DEFAULT_COUNTRY,
        content_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Title]:
        """
        Get top rated titles for a streaming service.
        
        Args:
            service: Service ID
            country: Country code
            content_type: Filter by type (movie or series)
            limit: Maximum number of results
            
        Returns:
            List of Title objects sorted by IMDB rating
        """
        result = await self.get_catalog_by_service(
            service=service,
            country=country,
            content_type=content_type,
            page_size=min(limit, MAX_PAGE_SIZE),
            order_by="rating"
        )
        
        return result["titles"][:limit]
    
    async def get_multi_service_catalog(
        self,
        services: List[str],
        country: str = DEFAULT_COUNTRY,
        content_type: Optional[str] = None,
        min_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get catalog from multiple services and find unique/overlapping titles.
        
        Args:
            services: List of service IDs
            country: Country code
            content_type: Filter by type
            min_rating: Minimum IMDB rating
            
        Returns:
            Dictionary with combined catalog and overlap statistics
        """
        service_ids = [SERVICE_API_IDS.get(s, s) for s in services]
        
        params = {
            "country": country,
            "catalogs": ",".join(service_ids),
            "order_by": "rating",
            "order_direction": "desc",
            "output_language": "en"
        }
        
        if content_type:
            params["show_type"] = content_type
        
        if min_rating is not None:
            params["rating_min"] = int(min_rating * 10)
        
        try:
            data = await self._make_request("shows/search/filters", params)
            shows = data.get("shows", [])
            titles = [self._parse_title(show, country) for show in shows]
            
            # Calculate service overlap
            service_counts = {s: 0 for s in services}
            for title in titles:
                for opt in title.streaming_options:
                    if opt.service in services:
                        service_counts[opt.service] += 1
            
            return {
                "titles": titles,
                "total_unique_titles": len(titles),
                "service_counts": service_counts
            }
            
        except Exception as e:
            logger.error(f"Error fetching multi-service catalog: {str(e)}")
            raise
    
    async def compare_services(
        self,
        services: List[str],
        country: str = DEFAULT_COUNTRY
    ) -> Dict[str, Any]:
        """
        Compare catalogs between multiple streaming services.
        
        Args:
            services: List of service IDs to compare
            country: Country code
            
        Returns:
            Comparison statistics including catalog sizes and overlap
        """
        # Fetch catalogs concurrently
        tasks = [
            self.get_catalog_by_service(service, country, page_size=100)
            for service in services
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        service_data = {}
        all_imdb_ids = {}
        
        for service, result in zip(services, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {service}: {str(result)}")
                continue
            
            titles = result.get("titles", [])
            service_data[service] = {
                "name": STREAMING_SERVICES.get(service, {}).get("name", service),
                "total_titles": len(titles),
                "avg_imdb_rating": sum(t.imdb_rating or 0 for t in titles) / len(titles) if titles else 0,
                "movies": len([t for t in titles if t.type == "movie"]),
                "series": len([t for t in titles if t.type == "series"])
            }
            
            # Track IMDB IDs for overlap calculation
            for title in titles:
                if title.imdb_id:
                    if title.imdb_id not in all_imdb_ids:
                        all_imdb_ids[title.imdb_id] = []
                    all_imdb_ids[title.imdb_id].append(service)
        
        # Calculate overlaps
        overlap_stats = {
            "unique_titles": len(all_imdb_ids),
            "multi_service_titles": len([k for k, v in all_imdb_ids.items() if len(v) > 1]),
            "all_services_titles": len([k for k, v in all_imdb_ids.items() if len(v) == len(services)])
        }
        
        return {
            "services": service_data,
            "overlap_stats": overlap_stats
        }
