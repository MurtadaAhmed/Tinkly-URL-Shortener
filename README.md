# URL-Shortener

Run the app with
uvicorn main:app --reload


1. Send POST request to /shorten/:
```json
{
  "long_url": "https://example.com"
}
```
response:
```json
{
  "short_url": "http://127.0.0.1:8000/abc123"
}

```
2. visit http://127.0.0.1:8000/abc123 to be redirected to https://example.com

3. statistics, send GET request to:
```
/abc123/stats
```

response:
```json
{
  "short_url": "http://127.0.0.1:8000/abc123",
  "long_url": "https://example.com",
  "visit_count": 1
}
```
