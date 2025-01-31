# URL-Shortener

A. Run locally for development:
```commandline
pip install -r requirements.txt
```
Run the app with:
```commandline
uvicorn main:app --reload --port 5000
```

B.Run with docker file:
```dockerfile
docker build -t url-shortener .
docker run -p 5000:5000 url-shortener
```


1. Send POST request to /shorten/ (can be tested using Swagger UI http://127.0.0.1:8000/docs):
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
