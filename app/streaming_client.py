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


def safe_get(data: Any, *keys, default=None):
    """Safely get nested values from dicts, handling None and missing keys."""
    result = data
    for key in keys:
        if result is None:
            return default
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
    return result if result is not None else default


def safe_get_name(item: Any) -> str:
    """Extract name from an item that could be a string, dict, or other."""
    if item is None:
        return ""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("name", "") or item.get("id", "") or ""
    return str(item)


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
    
    def _parse_streaming_option(self, option: Any) -> Optional[StreamingOption]:
        """Parse a single streaming option, handling various data formats."""
        if option is None:
            return None
        
        if not isinstance(option, dict):
            return None
        
        try:
            # Handle service being either a dict or string
            service_data = option.get("service")
            if isinstance(service_data, str):
                service_id = service_data
                service_name = service_data
            elif isinstance(service_data, dict):
                service_id = service_data.get("id", "") or ""
                service_name = service_data.get("name", "") or service_id
            else:
                service_id = ""
                service_name = ""
            
            return StreamingOption(
                service=service_id,
                service_name=service_name,
                type=option.get("type", "unknown") or "unknown",
                link=option.get("link"),
                quality=option.get("quality"),
                price=option.get("price"),
                available_since=option.get("availableSince"),
                leaving_soon=option.get("leavingSoon"),
                expiry_date=option.get("expiringDate") or option.get("expiring")
            )
        except Exception as e:
            logger.warning(f"Error parsing streaming option: {e}")
            return None

    def _parse_title(self, show_data: Any, country: str = DEFAULT_COUNTRY) -> Optional[Title]:
        """
        Parse API show data into a Title model.
        
        Args:
            show_data: Raw show data from the API
            country: Country code for streaming options
            
        Returns:
            Parsed Title object or None if parsing fails
        """
        if show_data is None or not isinstance(show_data, dict):
            return None
        
        try:
            # Extract streaming options for the specified country
            streaming_options = []
            streaming_info = safe_get(show_data, "streamingOptions", country, default=[])
            
            if isinstance(streaming_info, list):
                for option in streaming_info:
                    parsed = self._parse_streaming_option(option)
                    if parsed:
                        streaming_options.append(parsed)
            
            # Extract genres - handle list of strings or list of dicts
            genres = []
            raw_genres = show_data.get("genres", [])
            if isinstance(raw_genres, list):
                for g in raw_genres:
                    name = safe_get_name(g)
                    if name:
                        genres.append(name)
            
            # Extract cast - handle list of strings or list of dicts
            cast = []
            raw_cast = show_data.get("cast", [])
            if isinstance(raw_cast, list):
                for c in raw_cast[:10]:  # Limit to top 10
                    name = safe_get_name(c)
                    if name:
                        cast.append(name)
            
            # Extract directors - handle list of strings or list of dicts
            directors = []
            raw_directors = show_data.get("directors", [])
            if isinstance(raw_directors, list):
                for d in raw_directors:
                    name = safe_get_name(d)
                    if name:
                        directors.append(name)
            
            # Get poster and backdrop URLs - handle various structures
            poster_url = None
            backdrop_url = None
            image_set = show_data.get("imageSet")
            
            if isinstance(image_set, dict):
                # Try different poster paths
                vertical_poster = image_set.get("verticalPoster")
                if isinstance(vertical_poster, dict):
                    poster_url = vertical_poster.get("w480") or vertical_poster.get("w360") or vertical_poster.get("w240")
                elif isinstance(vertical_poster, str):
                    poster_url = vertical_poster
                
                # Try different backdrop paths
                horizontal_backdrop = image_set.get("horizontalBackdrop")
                if isinstance(horizontal_backdrop, dict):
                    backdrop_url = horizontal_backdrop.get("w720") or horizontal_backdrop.get("w480") or horizontal_backdrop.get("w360")
                elif isinstance(horizontal_backdrop, str):
                    backdrop_url = horizontal_backdrop
            
            # Fallback to direct poster/backdrop fields
            if not poster_url:
                poster_url = show_data.get("posterUrl") or show_data.get("poster")
            if not backdrop_url:
                backdrop_url = show_data.get("backdropUrl") or show_data.get("backdrop")
            
            # Get year - try multiple fields
            year = show_data.get("releaseYear") or show_data.get("firstAirYear") or show_data.get("year")
            if year and not isinstance(year, int):
                try:
                    year = int(year)
                except (ValueError, TypeError):
                    year = None
            
            # Get rating - handle different formats
            rating = show_data.get("rating")
            if rating is not None:
                try:
                    rating = float(rating)
                    # If rating is on 0-100 scale, convert to 0-10
                    if rating > 10:
                        rating = rating / 10
                except (ValueError, TypeError):
                    rating = None
            
            # Get vote count
            vote_count = show_data.get("ratingCount") or show_data.get("voteCount")
            if vote_count and not isinstance(vote_count, int):
                try:
                    vote_count = int(vote_count)
                except (ValueError, TypeError):
                    vote_count = None
            
            # Get runtime
            runtime = show_data.get("runtime")
            if runtime and not isinstance(runtime, int):
                try:
                    runtime = int(runtime)
                except (ValueError, TypeError):
                    runtime = None
            
            # Get TMDB ID
            tmdb_id = show_data.get("tmdbId")
            if tmdb_id is not None:
                tmdb_id = str(tmdb_id)
            
            return Title(
                id=str(show_data.get("id", "")) or "",
                imdb_id=show_data.get("imdbId"),
                tmdb_id=tmdb_id,
                title=show_data.get("title", "Unknown") or "Unknown",
                type=show_data.get("showType", "movie") or "movie",
                year=year,
                overview=show_data.get("overview"),
                genres=genres,
                imdb_rating=rating,
                imdb_vote_count=vote_count,
                runtime=runtime,
                poster_url=poster_url,
                backdrop_url=backdrop_url,
                directors=directors,
                cast=cast,
                streaming_options=streaming_options
            )
        except Exception as e:
            logger.error(f"Error parsing title: {e}")
            return None
    
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
        """
        service_id = SERVICE_API_IDS.get(service, service)
        
        params = {
            "country": country,
            "catalogs": service_id,
            "order_by": order_by,
            "order_direction": "desc" if order_by == "rating" else "asc",
            "limit": page_size

        }
        
        if content_type:
            params["show_type"] = content_type
        
        if min_rating is not None:
            params["rating_min"] = int(min_rating * 10)
        
        if max_rating is not None:
            params["rating_max"] = int(max_rating * 10)
        
        if genres:
            params["genres"] = ",".join(genres)
        
        params["output_language"] = "en"
        
        try:
            data = await self._make_request("shows/search/filters", params)
            
            shows = data.get("shows", []) if isinstance(data, dict) else []
            titles = []
            for show in shows:
                parsed = self._parse_title(show, country)
                if parsed:
                    titles.append(parsed)
            
            has_more = data.get("hasMore", False) if isinstance(data, dict) else False
            
            return {
                "titles": titles,
                "total_results": len(titles),
                "page": page,
                "page_size": page_size,
                "has_more": has_more,
                "cursor": data.get("nextCursor") if isinstance(data, dict) else None
            }
            
        except Exception as e:
            logger.error(f"Error fetching catalog for {service}: {str(e)}")
            raise
    
    async def get_title_by_imdb_id(
        self, 
        imdb_id: str, 
        country: str = DEFAULT_COUNTRY
    ) -> Optional[Title]:
        """Get a specific title by IMDB ID."""
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
        """Search for titles by name."""
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
            
            # Handle both list and dict responses
            if isinstance(data, list):
                shows = data
            elif isinstance(data, dict):
                shows = data.get("shows", []) or data.get("results", []) or []
            else:
                shows = []
            
            titles = []
            for show in shows:
                parsed = self._parse_title(show, country)
                if parsed:
                    titles.append(parsed)
            
            return titles
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
        """Get top rated titles for a streaming service."""
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
        """Get catalog from multiple services."""
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
            shows = data.get("shows", []) if isinstance(data, dict) else []
            
            titles = []
            for show in shows:
                parsed = self._parse_title(show, country)
                if parsed:
                    titles.append(parsed)
            
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
        """Compare catalogs between multiple streaming services."""
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
            ratings = [t.imdb_rating for t in titles if t.imdb_rating is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            service_data[service] = {
                "name": STREAMING_SERVICES.get(service, {}).get("name", service),
                "total_titles": len(titles),
                "avg_imdb_rating": avg_rating,
                "movies": len([t for t in titles if t.type == "movie"]),
                "series": len([t for t in titles if t.type == "series"])
            }
            
            for title in titles:
                if title.imdb_id:
                    if title.imdb_id not in all_imdb_ids:
                        all_imdb_ids[title.imdb_id] = []
                    all_imdb_ids[title.imdb_id].append(service)
        
        overlap_stats = {
            "unique_titles": len(all_imdb_ids),
            "multi_service_titles": len([k for k, v in all_imdb_ids.items() if len(v) > 1]),
            "all_services_titles": len([k for k, v in all_imdb_ids.items() if len(v) == len(services)])
        }
        
        return {
            "services": service_data,
            "overlap_stats": overlap_stats
        }
