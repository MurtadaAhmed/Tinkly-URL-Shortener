import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.asyncio
def test_homepage():
    # test if the home page loads successfully by checking status code and returned text
    response = client.get("/")
    assert response.status_code == 200
    assert "Tinkly-URL-Shortener" in response.text



@pytest.mark.asyncio
def test_shorten_url():
    # test url shortening returning 200 status and short_url in the json response
    response = client.post("/shorten/", json={"long_url": "https://google.com", "owner_id": None})
    assert response.status_code == 200
    assert "short_url" in response.json()


@pytest.mark.asyncio
def test_redirect():
    """
    create shortened url, extract the short code and access it
    check first if history has at least one redirect response and is the first one
    check if the destination is the actual website
    check if the status code for the destination is 200 (assuming the destination website works, Google)
    """
    response = client.post("/shorten/", json={"long_url": "https://google.com/"})
    json_response = response.json() # {"short_url": "http://test/abc123" }
    shortened_link = json_response["short_url"] # "http://test/abc123"
    short_code = shortened_link.split("/")[-1] # abc123

    redirect_response = client.get(f"/{short_code}")
    assert len(redirect_response.history) > 0
    assert redirect_response.history[0].status_code == 307
    assert redirect_response.history[0].headers["location"] == "https://google.com/"
    assert redirect_response.status_code == 200

@pytest.mark.asyncio
def test_stats():
    """
    - extract the shortened code
    - access the shorted code to increase the visit count to be tested
    - check if short_url, long_url, visit_count exist in the stat page for the shortened url
    - check if the visit_count is increased by 1
    """
    response = client.post("/shorten/", json={"long_url": "https://google.com/"})
    json_response = response.json()
    shortened_url = json_response["short_url"]
    short_code = shortened_url.split("/")[-1]
    client.get(f"/{short_code}")
    stats_response = client.get(f"/{short_code}/stats")

    json_stats_response = stats_response.json()

    assert "short_url" in json_stats_response
    assert "long_url" in json_stats_response
    assert "visit_count" in json_stats_response

    assert json_stats_response["visit_count"] == 1

