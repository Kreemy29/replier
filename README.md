# Replier - Thread Reply Generator

An AI-powered reply generator for creating witty, contextual responses to social media threads. Built with FastAPI and DeepSeek AI.

## Features

- Generate short, engaging replies (≤12 words) with emoji
- Fallback to predefined comments when needed
- Built-in content filtering to ensure appropriate responses
- Cross-origin support (CORS enabled)
- Comprehensive logging
- Simple API interface

## Installation

1. Clone the repository:
```
git clone https://github.com/Kreemy29/replier.git
cd replier
```

2. Set up a virtual environment:
```
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```
pip install -e .
```

4. Create a `.env` file with your DeepSeek API key:
```
DEEPSEEK_API_KEY=your-api-key-here
```

## Usage

### Starting the server

```
uvicorn app.main:app --reload --port 8004
```

### API Endpoint

The API has a single endpoint:

- **POST** `/generate-reply`

### Request Format

Send a POST request with the following JSON structure:

```json
{
  "original": {
    "username": "username_of_original_poster",
    "text": "The original post content"
  },
  "target": {
    "username": "username_of_target",
    "text": "The target post that you're replying to"
  },
  "history": [
    {
      "username": "other_user",
      "text": "Optional previous replies in the thread"
    }
  ]
}
```

**Important**: Both `original.text` and `target.text` must not be empty, or the service will return a fallback reply.

### Example Request

```bash
curl -X POST "http://localhost:8004/generate-reply" \
  -H "Content-Type: application/json" \
  -d '{
    "original": {
      "username": "urban_explorer22",
      "text": "Caught the city skyline from the rooftop lounge tonight—could use a partner in crime for the next late-night adventure 😏"
    },
    "target": {
      "username": "city_siren",
      "text": "Count me in! I know a hidden speakeasy with your name on it 🥂 #RooftopRomance"
    },
    "history": []
  }'
```

### Example Response

```json
{
  "reply": "Lead the way—I'm always up for secret hideouts! 🥂"
}
```

## Testing

The project includes several test scripts:

- `test_reply_service.py` - Tests the reply service directly
- `test_proper_request.py` - Tests the API with a proper request
- `test_reply_cleaning.py` - Tests the content filtering
- `test_extreme_cases.py` - Tests handling of edge cases
- `test_cors_client.html` - Browser-based test client

## License

MIT

## Author

Kreemy29
