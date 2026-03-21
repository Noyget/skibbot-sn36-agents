# SkibBot SN36 Agents

Web automation agents for Bittensor Subnet 36 (Autoppia).

## Agents

- **FormNavigator**: Navigate and fill web forms automatically
- **ScreenshotAnalyzer**: Analyze web page screenshots and identify elements
- **DataExtractor**: Extract structured data from web pages
- **WebActions**: Execute web navigation sequences

## Running

### Local Development
```bash
pip install -r requirements.txt
python -m agents.server
```

The agent server will expose an HTTP `/act` endpoint on port 8000.

### Docker (for validators)
```bash
docker build -t skibbot-sn36-agents .
docker run -p 8000:8000 skibbot-sn36-agents
```

## Testing

```bash
pytest test_form_navigator.py
pytest test_screenshot_analyzer.py
```

## Agent Protocol

Each agent accepts a task via HTTP POST to `/act`:

```json
{
  "task": "Navigate to example.com and fill in the login form",
  "environment": {
    "screenshot": "<base64_encoded_screenshot>",
    "url": "https://example.com",
    "viewport": {"width": 1920, "height": 1080}
  }
}
```

Response:
```json
{
  "actions": [
    {"type": "click", "selector": "#login-button"},
    {"type": "type", "selector": "#email", "text": "user@example.com"},
    {"type": "press", "key": "Tab"},
    {"type": "wait", "timeout": 2000}
  ]
}
```

## Registration

This agent repo is registered with SkibBot's Bittensor miner (UID 98, Subnet 36).

Validators can clone this repo and run agents via Docker to evaluate task performance.
