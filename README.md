# curl_cffi Scraper API

A FastAPI-based HTTP service that provides web scraping capabilities using curl_cffi to impersonate browser fingerprints and bypass anti-bot protection.

## Features

- **Browser Impersonation**: Uses curl_cffi to mimic real browser TLS/JA3 and HTTP/2 fingerprints
- **Anti-Bot Bypass**: Automatically bypasses fingerprint-based blocking (Cloudflare, Akamai, etc.)
- **FastAPI Framework**: High-performance async API with automatic documentation
- **Request Validation**: Pydantic models for robust input/output validation
- **Comprehensive Error Handling**: Detailed error messages and logging
- **Interactive Documentation**: Built-in Swagger UI and ReDoc

## Requirements

- Python 3.9+
- See `requirements.txt` for package dependencies

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cloudscraper_api
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Mode

Run with auto-reload enabled:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the built-in runner:

```bash
python -m app.main
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check

**GET** `/health`

Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Scrape URL

**POST** `/scrape`

Scrapes a web page using curl_cffi with Chrome browser impersonation.

**Request Body:**
```json
{
  "url": "https://example.com",
  "method": "GET",
  "headers": {
    "User-Agent": "Custom User Agent"
  },
  "timeout": 30,
  "data": {}
}
```

**Parameters:**
- `url` (required): The URL to scrape (must start with http:// or https://)
- `method` (optional): HTTP method - "GET" or "POST" (default: "GET")
- `headers` (optional): Custom HTTP headers as key-value pairs
- `timeout` (optional): Request timeout in seconds, 1-120 (default: 30)
- `data` (optional): Data to send with POST requests

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "status_code": 200,
  "content": "<!DOCTYPE html>...",
  "headers": {
    "content-type": "text/html; charset=UTF-8",
    "server": "nginx"
  },
  "elapsed_seconds": 1.234,
  "error": null
}
```

## Usage Examples

### Using cURL

```bash
# Simple GET request
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }'

# GET request with custom headers and timeout
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "method": "GET",
    "headers": {
      "User-Agent": "Mozilla/5.0"
    },
    "timeout": 60
  }'
```

### Using Python requests

```python
import requests

# Simple GET request
response = requests.post(
    "http://localhost:8000/scrape",
    json={
        "url": "https://example.com"
    }
)
result = response.json()
print(f"Status: {result['status_code']}")
print(f"Content length: {len(result['content'])}")

# POST request with data
response = requests.post(
    "http://localhost:8000/scrape",
    json={
        "url": "https://httpbin.org/post",
        "method": "POST",
        "data": {
            "key": "value"
        },
        "timeout": 30
    }
)
```

### Using JavaScript (fetch)

```javascript
// Simple GET request
fetch('http://localhost:8000/scrape', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://example.com',
    method: 'GET',
    timeout: 30
  })
})
.then(response => response.json())
.then(data => {
  console.log('Success:', data.success);
  console.log('Status Code:', data.status_code);
  console.log('Content:', data.content);
})
.catch(error => console.error('Error:', error));
```

## Project Structure

```
cloudscraper_api/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application and endpoints
│   ├── models.py            # Pydantic models for validation
│   └── scraper.py           # curl_cffi scraper service logic
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Important Notes

- **Browser Impersonation**: curl_cffi impersonates Chrome browser fingerprints to bypass anti-bot protection
- **Performance**: curl_cffi is significantly faster than traditional libraries like requests or httpx
- **Protocol Support**: Supports HTTP/2 and HTTP/3 (available since curl_cffi v0.11.4)
- **Rate Limiting**: Consider implementing rate limiting for production use to prevent abuse
- **Security**: The API currently allows scraping any URL. For production, consider:
  - Adding authentication (API keys, OAuth, etc.)
  - Implementing URL allowlists/blocklists
  - Adding rate limiting per user/IP
  - Validating URLs to prevent SSRF attacks
- **Active Maintenance**: curl_cffi is actively maintained with regular updates and new features

## Error Handling

The API handles various error scenarios:

- **Timeout errors**: Request exceeds specified timeout
- **Too many redirects**: URL causes redirect loop
- **HTTP errors**: Server returns error status codes
- **Network errors**: Connection issues, DNS failures
- **Invalid URLs**: Malformed or non-http(s) URLs

All errors are returned with detailed error messages in the response.

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Logging

The application uses Python's built-in logging. Logs include:
- Request information (URL, method)
- Success/failure status
- Error details with stack traces
- Performance metrics (elapsed time)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
