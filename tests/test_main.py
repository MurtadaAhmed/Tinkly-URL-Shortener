import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, User
import os
from pathlib import Path

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


@pytest.mark.asyncio
def test_shorten_invalid_url():
    """Test invalid URL shortening"""
    response = client.post("/shorten/", json={"long_url": "www.google.com", "owner_id": None})
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
def test_non_existent_url():
    """Test short url invalid returns 404"""
    response = client.get("/some123none2256existing")
    assert response.status_code == 404
    assert "detail" in response.json()

@pytest.mark.asyncio
def test_stats_non_existent_url():
    """Test no stats for invalid url returns 404"""
    response = client.get("/nonexistent/stats")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
def test_register_existing_username():
    """Test registering with existing username returns 400"""
    client.post("/register/", data={"username": "testuser", "password": "testpass"})
    response = client.post("/register/", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 400
    assert "detail" in response.json()

@pytest.mark.asyncio
def test_login_invalid_credentials():
    """Test login with invalid credentials return 401"""
    response = client.post("/login/", data={"username": "nonexistent", "password": "wrongpass"})
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
def test_admin_panel_non_admin():
    """Test normal user accessing admin page return 403"""
    client.post("/register/", data={"username": "testuser", "password": "testpass"})
    client.post("/login/", data={"username": "testuser", "password": "testpass"})

    response = client.get("/admin/")
    assert response.status_code == 403
    assert "detail" in response.json()
    client.get("/logout/")

@pytest.mark.asyncio
def test_dashboard_non_logged_in_redirected_to_homepage():
    """Test guest users been redirected to home page when accessing dashboard"""
    response = client.get("/dashboard/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_logout():
    """Test logout functionally, redirection with 303 status code, and 303 when accessing the dashboard after that"""
    client.post("/register/", data={"username": "testuser100", "password": "testpass100"})
    client.post("/login/", data={"username": "testuser100", "password": "testpass100"})

    # Log out the user
    response = client.get("/logout/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    dashboard_response = client.get("/dashboard/", follow_redirects=False)
    assert dashboard_response.status_code == 303
    assert dashboard_response.headers["location"] == "/"

