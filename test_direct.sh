#!/bin/bash
# =============================================================================
# Direct API Test Script
# Tests the Streaming Availability API directly via curl
# =============================================================================

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  STREAMING AVAILABILITY API - DIRECT TEST                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check for API key
if [ -z "$RAPIDAPI_KEY" ]; then
    echo "❌ ERROR: RAPIDAPI_KEY environment variable not set!"
    echo ""
    echo "To run this test:"
    echo "  1. Get a free API key from:"
    echo "     https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability"
    echo ""
    echo "  2. Set the environment variable:"
    echo "     export RAPIDAPI_KEY='your_api_key_here'"
    echo ""
    echo "  3. Run this script again:"
    echo "     ./test_direct.sh"
    exit 1
fi

echo "Using API key: ${RAPIDAPI_KEY:0:8}..."
echo ""

# =============================================================================
# Test 1: Search for a movie by title
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 TEST 1: Search for 'Inception'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

curl -s --request GET \
    --url 'https://streaming-availability.p.rapidapi.com/shows/search/title?country=us&title=Inception&output_language=en' \
    --header "X-RapidAPI-Key: $RAPIDAPI_KEY" \
    --header 'X-RapidAPI-Host: streaming-availability.p.rapidapi.com' | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
if isinstance(data, list) and len(data) > 0:
    show = data[0]
    print(f\"✅ Found: {show.get('title', 'N/A')} ({show.get('releaseYear', 'N/A')})\")
    print(f\"   IMDB ID: {show.get('imdbId', 'N/A')}\")
    print(f\"   ⭐ IMDB Rating: {show.get('rating', 'N/A')}/10\")
    print(f\"   Genres: {', '.join([g['name'] for g in show.get('genres', [])])}\")
    
    # Show streaming options
    streaming = show.get('streamingOptions', {}).get('us', [])
    services = set([opt['service']['name'] for opt in streaming])
    print(f\"   Available on: {', '.join(services) if services else 'N/A'}\")
else:
    print('⚠️ No results or error in response')
    print(data)
"

echo ""

# =============================================================================
# Test 2: Get Netflix catalog (top rated)
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📺 TEST 2: Netflix Catalog - Top 5 by IMDB Rating"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

curl -s --request GET \
    --url 'https://streaming-availability.p.rapidapi.com/shows/search/filters?country=us&catalogs=netflix&order_by=rating&order_direction=desc&output_language=en' \
    --header "X-RapidAPI-Key: $RAPIDAPI_KEY" \
    --header 'X-RapidAPI-Host: streaming-availability.p.rapidapi.com' | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
shows = data.get('shows', [])[:5]
print(f'✅ Found {len(data.get(\"shows\", []))} titles on Netflix\n')
print('Top 5 by IMDB Rating:')
print('-' * 50)
for i, show in enumerate(shows, 1):
    title = show.get('title', 'N/A')
    year = show.get('releaseYear') or show.get('firstAirYear', 'N/A')
    rating = show.get('rating', 'N/A')
    show_type = show.get('showType', 'N/A')
    imdb_id = show.get('imdbId', 'N/A')
    print(f\"{i}. {title} ({year})\")
    print(f\"   Type: {show_type} | IMDB: {imdb_id} | ⭐ {rating}/10\")
"

echo ""

# =============================================================================
# Test 3: Get a specific movie by IMDB ID
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎬 TEST 3: Lookup 'The Shawshank Redemption' (tt0111161)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

curl -s --request GET \
    --url 'https://streaming-availability.p.rapidapi.com/shows/tt0111161?country=us&output_language=en' \
    --header "X-RapidAPI-Key: $RAPIDAPI_KEY" \
    --header 'X-RapidAPI-Host: streaming-availability.p.rapidapi.com' | \
    python3 -c "
import sys, json
show = json.load(sys.stdin)
if 'title' in show:
    print(f\"✅ {show.get('title', 'N/A')} ({show.get('releaseYear', 'N/A')})\")
    print(f\"   IMDB ID: {show.get('imdbId', 'N/A')}\")
    print(f\"   ⭐ IMDB Rating: {show.get('rating', 'N/A')}/10 ({show.get('ratingCount', 0):,} votes)\")
    print(f\"   Runtime: {show.get('runtime', 'N/A')} minutes\")
    print(f\"   Genres: {', '.join([g['name'] for g in show.get('genres', [])])}\")
    
    # Show all streaming options
    streaming = show.get('streamingOptions', {}).get('us', [])
    if streaming:
        print(f'   Streaming options:')
        seen = set()
        for opt in streaming:
            svc = opt['service']['name']
            opt_type = opt.get('type', 'unknown')
            if svc not in seen:
                print(f\"      • {svc} ({opt_type})\")
                seen.add(svc)
    else:
        print('   Streaming: Not currently available in US')
else:
    print('⚠️ Error or not found')
    print(show)
"

echo ""

# =============================================================================
# Test 4: Compare multiple services
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 TEST 4: Multi-service query (Netflix + Prime + Disney+)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

curl -s --request GET \
    --url 'https://streaming-availability.p.rapidapi.com/shows/search/filters?country=us&catalogs=netflix,prime,disney&rating_min=80&order_by=rating&order_direction=desc&output_language=en' \
    --header "X-RapidAPI-Key: $RAPIDAPI_KEY" \
    --header 'X-RapidAPI-Host: streaming-availability.p.rapidapi.com' | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
shows = data.get('shows', [])
print(f'✅ Found {len(shows)} titles with IMDB rating >= 8.0')
print('')
print('Sample titles (first 5):')
print('-' * 50)
for show in shows[:5]:
    title = show.get('title', 'N/A')
    rating = show.get('rating', 'N/A')
    streaming = show.get('streamingOptions', {}).get('us', [])
    services = list(set([opt['service']['name'] for opt in streaming]))[:3]
    print(f\"• {title} (⭐ {rating}) - {', '.join(services)}\")
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL TESTS COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
