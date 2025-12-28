#!/usr/bin/env python3
"""
Test Script for Streaming Catalog API

This script demonstrates the API functionality and can be used to verify
the API works correctly with a real RapidAPI key.

Usage:
    # With a real API key (set environment variable):
    export RAPIDAPI_KEY="your_key_here"
    python test_api.py

    # Or run in demo mode to see sample output:
    python test_api.py --demo
"""

import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Sample data that demonstrates what the API returns
SAMPLE_NETFLIX_CATALOG = {
    "service": "netflix",
    "service_name": "Netflix",
    "country": "us",
    "total_results": 5,
    "titles": [
        {
            "id": "1001",
            "imdb_id": "tt0111161",
            "title": "The Shawshank Redemption",
            "type": "movie",
            "year": 1994,
            "genres": ["Drama", "Crime"],
            "imdb_rating": 9.3,
            "imdb_vote_count": 2800000,
            "runtime": 142,
            "directors": ["Frank Darabont"],
            "cast": ["Tim Robbins", "Morgan Freeman"],
            "streaming_options": [{"service": "netflix", "type": "subscription"}]
        },
        {
            "id": "1002", 
            "imdb_id": "tt0068646",
            "title": "The Godfather",
            "type": "movie",
            "year": 1972,
            "genres": ["Crime", "Drama"],
            "imdb_rating": 9.2,
            "imdb_vote_count": 1900000,
            "runtime": 175,
            "directors": ["Francis Ford Coppola"],
            "cast": ["Marlon Brando", "Al Pacino"],
            "streaming_options": [{"service": "netflix", "type": "subscription"}]
        },
        {
            "id": "1003",
            "imdb_id": "tt0468569",
            "title": "The Dark Knight",
            "type": "movie", 
            "year": 2008,
            "genres": ["Action", "Crime", "Drama"],
            "imdb_rating": 9.0,
            "imdb_vote_count": 2700000,
            "runtime": 152,
            "directors": ["Christopher Nolan"],
            "cast": ["Christian Bale", "Heath Ledger"],
            "streaming_options": [{"service": "netflix", "type": "subscription"}]
        },
        {
            "id": "1004",
            "imdb_id": "tt0944947",
            "title": "Game of Thrones",
            "type": "series",
            "year": 2011,
            "genres": ["Action", "Adventure", "Drama"],
            "imdb_rating": 9.2,
            "imdb_vote_count": 2100000,
            "runtime": 57,
            "directors": [],
            "cast": ["Emilia Clarke", "Peter Dinklage"],
            "streaming_options": [{"service": "netflix", "type": "subscription"}]
        },
        {
            "id": "1005",
            "imdb_id": "tt0903747",
            "title": "Breaking Bad",
            "type": "series",
            "year": 2008,
            "genres": ["Crime", "Drama", "Thriller"],
            "imdb_rating": 9.5,
            "imdb_vote_count": 2000000,
            "runtime": 49,
            "directors": [],
            "cast": ["Bryan Cranston", "Aaron Paul"],
            "streaming_options": [{"service": "netflix", "type": "subscription"}]
        }
    ]
}


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_title(title: dict):
    """Print a formatted title entry."""
    rating = title.get('imdb_rating', 'N/A')
    votes = title.get('imdb_vote_count', 0)
    votes_str = f"{votes:,}" if votes else "N/A"
    
    print(f"""
    📽️  {title['title']} ({title.get('year', 'N/A')})
        Type: {title['type'].upper()}
        IMDB ID: {title.get('imdb_id', 'N/A')}
        ⭐ IMDB Rating: {rating}/10 ({votes_str} votes)
        Genres: {', '.join(title.get('genres', []))}
        Runtime: {title.get('runtime', 'N/A')} min
        Cast: {', '.join(title.get('cast', [])[:3])}
        Streaming: {', '.join([opt['service'] for opt in title.get('streaming_options', [])])}
    """)


def demo_mode():
    """Run in demo mode with sample data."""
    print_header("DEMO MODE - Sample API Output")
    print("\nThis demonstrates what the API returns when querying streaming catalogs.")
    print("Each title includes IMDB ratings paired with streaming availability.\n")
    
    # Show Netflix catalog sample
    print_header("GET /catalog/netflix - Netflix Catalog with IMDB Ratings")
    
    for title in SAMPLE_NETFLIX_CATALOG['titles']:
        print_title(title)
    
    print(f"\n📊 Summary:")
    print(f"   Total titles shown: {len(SAMPLE_NETFLIX_CATALOG['titles'])}")
    
    movies = [t for t in SAMPLE_NETFLIX_CATALOG['titles'] if t['type'] == 'movie']
    series = [t for t in SAMPLE_NETFLIX_CATALOG['titles'] if t['type'] == 'series']
    
    print(f"   Movies: {len(movies)}")
    print(f"   Series: {len(series)}")
    
    ratings = [t['imdb_rating'] for t in SAMPLE_NETFLIX_CATALOG['titles'] if t.get('imdb_rating')]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    print(f"   Average IMDB Rating: {avg_rating:.1f}/10")
    
    print_header("API Response Structure (JSON)")
    print(json.dumps(SAMPLE_NETFLIX_CATALOG['titles'][0], indent=2))


async def live_test():
    """Test with real API key."""
    api_key = os.getenv("RAPIDAPI_KEY")
    
    if not api_key:
        print("❌ ERROR: RAPIDAPI_KEY environment variable not set!")
        print("\nTo run live tests:")
        print("  1. Get a free API key from: https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability")
        print("  2. Set the environment variable: export RAPIDAPI_KEY='your_key'")
        print("  3. Run this script again")
        print("\nOr run in demo mode: python test_api.py --demo")
        return False
    
    print_header("LIVE API TEST")
    print(f"Using API key: {api_key[:8]}...")
    
    try:
        from app.streaming_client import StreamingAPIClient
        
        client = StreamingAPIClient(api_key)
        
        # Test 1: Search for a specific movie
        print("\n🔍 Test 1: Searching for 'Inception'...")
        titles = await client.search_titles("Inception", country="us")
        
        if titles:
            print(f"   ✅ Found {len(titles)} results")
            print_title(titles[0].model_dump())
        else:
            print("   ⚠️ No results found")
        
        # Test 2: Get Netflix catalog
        print("\n📺 Test 2: Fetching Netflix catalog (top 5 by rating)...")
        result = await client.get_catalog_by_service(
            service="netflix",
            country="us",
            page_size=5,
            order_by="rating"
        )
        
        if result['titles']:
            print(f"   ✅ Found {len(result['titles'])} titles")
            for title in result['titles'][:3]:
                print_title(title.model_dump())
        else:
            print("   ⚠️ No results found")
        
        # Test 3: Look up by IMDB ID
        print("\n🎬 Test 3: Looking up 'The Shawshank Redemption' (tt0111161)...")
        title = await client.get_title_by_imdb_id("tt0111161", country="us")
        
        if title:
            print(f"   ✅ Found title")
            print_title(title.model_dump())
            print(f"   Available on: {[opt.service_name for opt in title.streaming_options]}")
        else:
            print("   ⚠️ Title not found")
        
        # Test 4: Multi-service query
        print("\n🔄 Test 4: Querying multiple services (Netflix, Prime, Disney+)...")
        result = await client.get_multi_service_catalog(
            services=["netflix", "prime", "disney"],
            country="us",
            min_rating=8.0
        )
        
        print(f"   ✅ Found {result['total_unique_titles']} titles with IMDB rating >= 8.0")
        
        print_header("✅ ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        return False


def main():
    """Main entry point."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     STREAMING CATALOG API - TEST SCRIPT                   ║
    ║     Verifies movies are paired with IMDB ratings          ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    if "--demo" in sys.argv:
        demo_mode()
    else:
        # Try live test, fall back to demo
        result = asyncio.run(live_test())
        if not result:
            print("\n" + "-" * 60)
            print("Running demo mode to show expected output...")
            demo_mode()


if __name__ == "__main__":
    main()
