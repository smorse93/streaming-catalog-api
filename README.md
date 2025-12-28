# Streaming Catalog API with IMDB Ratings

A comprehensive FastAPI backend that aggregates streaming service catalogs from major platforms and pairs them with IMDB ratings. Get real-time data about what's available to watch on Netflix, Prime Video, Peacock, Disney+, Apple TV+, and HBO Max (Max).

## Features

- 📺 **Full Catalog Access**: Get complete catalogs for each streaming service
- ⭐ **IMDB Ratings**: Every title includes IMDB rating and vote count
- 🔍 **Powerful Search**: Search across all services simultaneously
- 📊 **Service Comparison**: Compare catalogs between services
- 🏆 **Top Rated**: Get the highest-rated content on each platform
- 🎭 **Genre Filtering**: Filter by genre, year, rating, and content type
- 🌍 **Multi-Region**: Support for 60+ countries

## Supported Streaming Services

| Service | ID | Description |
|---------|-----|-------------|
| Netflix | `netflix` | Netflix streaming service |
| Prime Video | `prime` | Amazon Prime Video |
| Disney+ | `disney` | Disney Plus |
| Max (HBO Max) | `hbo` | Max (formerly HBO Max) |
| Peacock | `peacock` | NBC's Peacock |
| Apple TV+ | `apple` | Apple TV Plus |

## Quick Start

### 1. Installation

```bash
# Clone or copy the project
cd streaming-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get Your API Key

This API uses the **Streaming Availability API** via RapidAPI as its data source:

1. Go to [RapidAPI - Streaming Availability](https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability)
2. Sign up for a free account (100 requests/day free tier)
3. Subscribe to the API and copy your API key

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your RapidAPI key
RAPIDAPI_KEY=your_actual_api_key_here
```

### 4. Run the Server

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

### 5. View Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Catalog Endpoints

#### Get Service Catalog
```http
GET /catalog/{service}
```

Get the complete catalog for a specific streaming service.

**Parameters:**
- `service` (path): Service ID (netflix, prime, disney, hbo, peacock, apple)
- `country` (query): Country code (default: us)
- `content_type` (query): Filter by type (movie, series)
- `min_rating` (query): Minimum IMDB rating (0-10)
- `max_rating` (query): Maximum IMDB rating (0-10)
- `genres` (query): Comma-separated genre names
- `page` (query): Page number
- `page_size` (query): Results per page (max 100)

**Example:**
```bash
curl "http://localhost:8000/catalog/netflix?country=us&content_type=movie&min_rating=7.5"
```

#### Get Multi-Service Catalog
```http
GET /catalog
```

Get combined catalog from multiple services.

**Example:**
```bash
curl "http://localhost:8000/catalog?services=netflix,prime,disney&min_rating=8.0"
```

### Top Movies Endpoints

#### Get Top X Movies for a Service
```http
GET /top-movies/{service}?limit={number}
```

Get the top X highest-rated movies on any streaming service.

**Parameters:**
- `service` (path): Service ID (netflix, prime, disney, hbo, peacock, apple)
- `limit` (query): Number of movies to return (1-100, default: 10)
- `min_rating` (query): Minimum IMDB rating filter (0-10)
- `genre` (query): Filter by genre (Action, Comedy, Drama, etc.)
- `country` (query): Country code (default: us)

**Examples:**
```bash
# Top 10 movies on Netflix
curl "http://localhost:8000/top-movies/netflix?limit=10"

# Top 25 movies on Prime Video with rating >= 7.5
curl "http://localhost:8000/top-movies/prime?limit=25&min_rating=7.5"

# Top 20 Animation movies on Disney+
curl "http://localhost:8000/top-movies/disney?limit=20&genre=Animation"

# Top 15 movies on HBO Max in UK
curl "http://localhost:8000/top-movies/hbo?limit=15&country=gb"
```

#### Get Top Movies Across ALL Services
```http
GET /top-movies?limit={number}
```

Get top movies from all streaming services in one call.

**Example:**
```bash
# Top 10 movies from each service with rating >= 7.0
curl "http://localhost:8000/top-movies?limit=10&min_rating=7.0"
```

### Top Rated Endpoints (Movies + Series)

#### Top Rated for Service
```http
GET /top-rated/{service}
```

**Example:**
```bash
curl "http://localhost:8000/top-rated/netflix?content_type=movie&limit=25"
```

#### Top Rated Across All Services
```http
GET /top-rated
```

**Example:**
```bash
curl "http://localhost:8000/top-rated?limit=10"
```

### Search Endpoints

#### Search Titles
```http
GET /search
```

**Parameters:**
- `q` (query): Search query (required)
- `services` (query): Comma-separated service IDs
- `content_type` (query): movie or series

**Example:**
```bash
curl "http://localhost:8000/search?q=inception&services=netflix,prime"
```

### Title Lookup

#### Get by IMDB ID
```http
GET /title/imdb/{imdb_id}
```

**Example:**
```bash
curl "http://localhost:8000/title/imdb/tt0111161"  # The Shawshank Redemption
```

### Comparison & Statistics

#### Compare Services
```http
GET /compare
```

**Example:**
```bash
curl "http://localhost:8000/compare?services=netflix,prime,disney"
```

#### Service Statistics
```http
GET /stats/{service}
```

**Example:**
```bash
curl "http://localhost:8000/stats/netflix"
```

## Response Examples

### Catalog Response
```json
{
  "service": "netflix",
  "service_name": "Netflix",
  "country": "us",
  "total_results": 50,
  "page": 1,
  "page_size": 25,
  "has_more": true,
  "titles": [
    {
      "id": "12345",
      "imdb_id": "tt0111161",
      "tmdb_id": "278",
      "title": "The Shawshank Redemption",
      "type": "movie",
      "year": 1994,
      "overview": "Two imprisoned men bond over...",
      "genres": ["Drama", "Crime"],
      "imdb_rating": 9.3,
      "imdb_vote_count": 2800000,
      "runtime": 142,
      "poster_url": "https://...",
      "directors": ["Frank Darabont"],
      "cast": ["Tim Robbins", "Morgan Freeman"],
      "streaming_options": [
        {
          "service": "netflix",
          "service_name": "Netflix",
          "type": "subscription",
          "link": "https://www.netflix.com/title/...",
          "quality": "uhd"
        }
      ]
    }
  ]
}
```

### Service Comparison Response
```json
{
  "country": "us",
  "services": {
    "netflix": {
      "name": "Netflix",
      "total_titles": 1500,
      "avg_imdb_rating": 6.8,
      "movies": 1000,
      "series": 500
    },
    "prime": {
      "name": "Amazon Prime Video",
      "total_titles": 2000,
      "avg_imdb_rating": 6.5,
      "movies": 1400,
      "series": 600
    }
  },
  "overlap_stats": {
    "unique_titles": 3200,
    "multi_service_titles": 300,
    "all_services_titles": 50
  }
}
```

## Architecture

```
streaming-api/
├── app/
│   ├── __init__.py         # Package initialization
│   ├── main.py             # FastAPI application & endpoints
│   ├── models.py           # Pydantic models
│   ├── config.py           # Configuration & constants
│   └── streaming_client.py # API client for Streaming Availability
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Data Flow

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   Client    │────▶│  FastAPI Server  │────▶│ Streaming Avail API │
│  (Your App) │     │  (This Backend)  │     │    (via RapidAPI)   │
└─────────────┘     └──────────────────┘     └─────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │    Cache     │
                    │ (1hr TTL)    │
                    └──────────────┘
```

## Rate Limits & Caching

- **Free Tier**: 100 requests/day to RapidAPI
- **Built-in Cache**: 1-hour TTL to minimize API calls
- **Paid Tiers**: Available for higher volume needs

## Error Handling

All errors return a consistent JSON structure:

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "status_code": 500
}
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RAPIDAPI_KEY` | Your RapidAPI key | Yes |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No |

## Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t streaming-api .
docker run -p 8000:8000 -e RAPIDAPI_KEY=your_key streaming-api
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [Streaming Availability API](https://www.movieofthenight.com/about/api) for providing comprehensive streaming data
- [IMDB](https://www.imdb.com/) for ratings data (provided through Streaming Availability API)
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
