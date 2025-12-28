"""
Streaming Service Configuration and Constants
"""

# Service IDs used by the Streaming Availability API
STREAMING_SERVICES = {
    "netflix": {
        "id": "netflix",
        "name": "Netflix",
        "description": "Netflix streaming service"
    },
    "prime": {
        "id": "prime",
        "name": "Amazon Prime Video", 
        "description": "Amazon Prime Video streaming service"
    },
    "disney": {
        "id": "disney",
        "name": "Disney+",
        "description": "Disney Plus streaming service"
    },
    "hbo": {
        "id": "hbo",
        "name": "Max (HBO Max)",
        "description": "Max (formerly HBO Max) streaming service"
    },
    "peacock": {
        "id": "peacock",
        "name": "Peacock",
        "description": "Peacock streaming service"
    },
    "apple": {
        "id": "apple",
        "name": "Apple TV+",
        "description": "Apple TV Plus streaming service"
    },
    "hulu": {
        "id": "hulu",
        "name": "Hulu",
        "description": "Hulu streaming service"
    }
}

# Alternative service ID mappings (the API uses slightly different IDs)
SERVICE_API_IDS = {
    "netflix": "netflix",
    "prime": "prime", 
    "disney": "disney",
    "hbo": "hbo",  # Max/HBO Max
    "peacock": "peacock",
    "apple": "apple",
    "hulu": "hulu"
}

# Supported countries (default to US)
DEFAULT_COUNTRY = "us"

# Content types
CONTENT_TYPES = ["movie", "series"]

# Default API settings
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100
